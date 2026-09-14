use ring::{
    aead, digest,
    rand::{SecureRandom, SystemRandom},
};

pub fn random<const N: usize>() -> [u8; N] {
    let mut bytes = [0; N];
    SystemRandom::new()
        .fill(&mut bytes)
        .expect("OS random source unavailable");
    bytes
}

pub fn hash(bytes: &[u8]) -> String {
    digest::digest(&digest::SHA256, bytes)
        .as_ref()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn cipher(key: &[u8; 32]) -> aead::LessSafeKey {
    aead::LessSafeKey::new(aead::UnboundKey::new(&aead::AES_256_GCM, key).unwrap())
}

pub fn seal(key: &[u8; 32], aad: &[u8], data: &[u8]) -> Result<Vec<u8>, String> {
    let nonce = random::<12>();
    let mut ciphertext = data.to_vec();
    cipher(key)
        .seal_in_place_append_tag(
            aead::Nonce::assume_unique_for_key(nonce),
            aead::Aad::from(aad),
            &mut ciphertext,
        )
        .map_err(|_| "Encryption failed")?;
    Ok([nonce.as_slice(), &ciphertext].concat())
}

pub fn open(key: &[u8; 32], aad: &[u8], data: &[u8]) -> Result<Vec<u8>, String> {
    if data.len() < 28 {
        return Err("Truncated encrypted state".into());
    }
    let nonce: [u8; 12] = data[..12].try_into().unwrap();
    let mut ciphertext = data[12..].to_vec();
    let plaintext = cipher(key)
        .open_in_place(
            aead::Nonce::assume_unique_for_key(nonce),
            aead::Aad::from(aad),
            &mut ciphertext,
        )
        .map_err(|_| "Authentication failed")?;
    Ok(plaintext.to_vec())
}
