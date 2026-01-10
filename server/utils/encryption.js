const CryptoJS = require('crypto-js');

const encryptionKey = process.env.ENCRYPTION_KEY;

if (!encryptionKey) {
  if (process.env.NODE_ENV === 'production') {
    throw new Error('ENCRYPTION_KEY must be set in production');
  }
  console.warn('WARNING: ENCRYPTION_KEY not set. Using default key for development only.');
}

// Validate key length in production
const key = encryptionKey || 'default-key-change-in-production';
if (process.env.NODE_ENV === 'production' && key.length < 32) {
  throw new Error('ENCRYPTION_KEY must be at least 32 characters in production');
}

const encrypt = (text) => {
  if (!text) return null;
  return CryptoJS.AES.encrypt(text, key).toString();
};

const decrypt = (encryptedText) => {
  if (!encryptedText) return null;
  const bytes = CryptoJS.AES.decrypt(encryptedText, key);
  return bytes.toString(CryptoJS.enc.Utf8);
};

module.exports = { encrypt, decrypt };
