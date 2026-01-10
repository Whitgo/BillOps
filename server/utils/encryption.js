const CryptoJS = require('crypto-js');

const encryptionKey = process.env.ENCRYPTION_KEY || 'default-key-change-in-production';

const encrypt = (text) => {
  if (!text) return null;
  return CryptoJS.AES.encrypt(text, encryptionKey).toString();
};

const decrypt = (encryptedText) => {
  if (!encryptedText) return null;
  const bytes = CryptoJS.AES.decrypt(encryptedText, encryptionKey);
  return bytes.toString(CryptoJS.enc.Utf8);
};

module.exports = { encrypt, decrypt };
