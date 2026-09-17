//! Persistent opaque ciphertext storage. Authentication belongs to recovery.
use std::{
    fs,
    io::Write,
    path::{Path, PathBuf},
};

pub struct Store {
    path: PathBuf,
    pub identity: String,
}
fn valid(id: &str) -> bool {
    id.len() == 64
        && id
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
impl Store {
    pub fn open(path: &Path) -> Result<Self, String> {
        fs::create_dir_all(path).map_err(|e| e.to_string())?;
        let identity_path = path.join("identity");
        match fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&identity_path)
        {
            Ok(mut file) => {
                file.write_all(crate::crypto::hash(&crate::crypto::random::<32>()).as_bytes())
                    .map_err(|e| e.to_string())?;
                file.sync_all().map_err(|e| e.to_string())?;
            }
            Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {}
            Err(e) => return Err(e.to_string()),
        }
        let identity = fs::read_to_string(identity_path).map_err(|e| e.to_string())?;
        if !valid(&identity) {
            return Err("Invalid persistent node identity".into());
        }
        Ok(Self {
            path: path.to_owned(),
            identity,
        })
    }
    fn unit_path(&self, id: &str) -> Result<PathBuf, String> {
        if !valid(id) {
            return Err("Invalid unit identifier".into());
        }
        Ok(self.path.join(format!("{id}.unit")))
    }
    pub fn get(&self, id: &str) -> Result<Vec<u8>, String> {
        let path = self.unit_path(id)?;
        let mut file = fs::File::open(path).map_err(|e| e.to_string())?;
        let mut bytes = Vec::new();
        use std::io::Read;
        (&mut file)
            .take(300_001)
            .read_to_end(&mut bytes)
            .map_err(|e| e.to_string())?;
        if bytes.len() > 300_000 {
            return Err("Ciphertext too large".into());
        }
        Ok(bytes)
    }
    pub fn put(&self, id: &str, bytes: &[u8]) -> Result<(), String> {
        let path = self.unit_path(id)?;
        if bytes.is_empty() || bytes.len() > 300_000 {
            return Err("Invalid ciphertext size".into());
        }
        let temporary = self.path.join(format!(
            "{}.tmp",
            crate::crypto::hash(&crate::crypto::random::<16>())
        ));
        let result = (|| -> std::io::Result<()> {
            let mut file = fs::OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&temporary)?;
            file.write_all(bytes)?;
            file.sync_all()?;
            drop(file);
            fs::rename(&temporary, &path)
        })();
        if result.is_err() {
            let _ = fs::remove_file(temporary);
        }
        result.map_err(|e| e.to_string())
    }
}
