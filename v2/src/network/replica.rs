//! Offline verified journal copies. Keep the expected head outside the replicas.
use super::{journal::Journal, Limits, Task};
use crate::crypto;
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
};

pub struct ReplicaPlan<'a> {
    pub tasks: &'a [Task],
    pub limits: Limits,
    pub key: &'a [u8; 32],
    pub backend: &'a str,
}
impl ReplicaPlan<'_> {
    fn verify(&self, path: &Path, head: &str) -> Result<(), String> {
        if !path.is_dir() {
            return Err("Replica directory missing".into());
        }
        let journal = Journal::open(path, self.key, self.tasks, self.limits, self.backend)?;
        if journal.head() != head {
            return Err("Replica differs from trusted checkpoint head".into());
        }
        Ok(())
    }
    /// Copy the first valid replica to a NEW journal directory, or create a backup.
    /// Call only with stopped writers and exclusive ownership of destination.
    /// The caller retains the key, full task/DNA plan and trusted head separately.
    /// This does not choose a latest version by majority or retry uncertain work.
    pub fn restore(
        &self,
        replicas: &[PathBuf],
        destination: &Path,
        expected_head: &str,
    ) -> Result<PathBuf, String> {
        if expected_head.len() != 64 || !expected_head.bytes().all(|b| b.is_ascii_hexdigit()) {
            return Err("A trusted SHA-256 checkpoint head is required".into());
        }
        if destination.exists() {
            return Err("Destination must not exist".into());
        }
        if replicas.is_empty() || replicas.len() > 16 {
            return Err("Expected 1..16 replicas".into());
        }
        let parent = destination
            .parent()
            .filter(|p| !p.as_os_str().is_empty())
            .unwrap_or(Path::new("."));
        let mut failures = Vec::new();
        for replica in replicas {
            if let Err(error) = self.verify(replica, expected_head) {
                failures.push(format!("{}: {error}", replica.display()));
                continue;
            }
            let staging = parent.join(format!(
                ".tron-restore-{}",
                crypto::hash(&crypto::random::<32>())
            ));
            fs::create_dir(&staging).map_err(|e| e.to_string())?;
            let copied = self
                .copy(replica, &staging)
                .and_then(|_| self.verify(&staging, expected_head));
            if let Err(error) = copied {
                fs::remove_dir_all(&staging).map_err(|e| e.to_string())?;
                failures.push(format!("{}: {error}", replica.display()));
                continue;
            }
            // Publish only after authenticating the actual copied bytes.
            if destination.exists() {
                fs::remove_dir_all(&staging).map_err(|e| e.to_string())?;
                return Err("Destination appeared during restore".into());
            }
            if let Err(error) = fs::rename(&staging, destination) {
                fs::remove_dir_all(&staging).map_err(|e| e.to_string())?;
                return Err(error.to_string());
            }
            return Ok(replica.clone());
        }
        Err(format!("No usable replica: {}", failures.join("; ")))
    }
    fn copy(&self, source: &Path, destination: &Path) -> Result<(), String> {
        let entries = fs::read_dir(source)
            .map_err(|e| e.to_string())?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| e.to_string())?;
        if entries.len() > 300 {
            return Err("Journal capacity exceeded".into());
        }
        for entry in entries {
            if !entry.file_type().map_err(|e| e.to_string())?.is_file()
                || entry.metadata().map_err(|e| e.to_string())?.len() > 16_777_216
            {
                return Err("Invalid replica entry".into());
            }
            let bytes = fs::read(entry.path()).map_err(|e| e.to_string())?;
            let mut file = fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(destination.join(entry.file_name()))
                .map_err(|e| e.to_string())?;
            file.write_all(&bytes)
                .and_then(|_| file.sync_all())
                .map_err(|e| e.to_string())?;
        }
        Ok(())
    }
}
