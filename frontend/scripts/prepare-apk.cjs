const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { pipeline } = require('node:stream/promises');
const { Readable } = require('node:stream');
const apk = path.join(__dirname, '../public/downloads/NusaGuard.apk');
async function main() {
  const fd = fs.openSync(apk, 'r');
  const head = Buffer.alloc(512);
  fs.readSync(fd, head, 0, 512, 0);
  fs.closeSync(fd);
  const pointer = head.toString('utf8');
  if (pointer.startsWith('version https://git-lfs.github.com/spec/v1')) {
    const oid = pointer.match(/oid sha256:([a-f0-9]{64})/)[1];
    const size = Number(pointer.match(/size (\d+)/)[1]);
    const ref = process.env.VERCEL_GIT_COMMIT_SHA || 'main';
    const url = `https://media.githubusercontent.com/media/novaauliya151/nusaguard/${encodeURIComponent(ref)}/frontend/public/downloads/NusaGuard.apk`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`APK download failed: HTTP ${response.status}`);
    const temp = apk + '.tmp';
    try {
      await pipeline(Readable.fromWeb(response.body), fs.createWriteStream(temp));
      const hash = crypto.createHash('sha256');
      for await (const chunk of fs.createReadStream(temp)) hash.update(chunk);
      if (fs.statSync(temp).size !== size || hash.digest('hex') !== oid) throw new Error('APK LFS size/hash mismatch');
      fs.renameSync(temp, apk);
    } finally { if (fs.existsSync(temp)) fs.unlinkSync(temp); }
  }
  const check = fs.openSync(apk, 'r');
  const magic = Buffer.alloc(4);
  fs.readSync(check, magic, 0, 4, 0);
  fs.closeSync(check);
  if (!magic.equals(Buffer.from([80,75,3,4]))) throw new Error('Download file is not an APK/ZIP');
  console.log(`APK verified: ${fs.statSync(apk).size} bytes`);
}
main().catch(error => { console.error(error); process.exit(1); });