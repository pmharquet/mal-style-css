// Capture d'un thème sur la copie locale de la liste (serveur du projet sur :8765).
// Usage : node tools/preview/shot.mjs <theme> [options]
//   --list anime|manga   liste à afficher (anime)
//   --status N           onglet : 7 all, 1 en cours, 2 completed, 3 on hold, 4 dropped, 6 planned
//   --scroll Y           défilement vertical en px avant la capture (0)
//   --row N              centre la Nième ligne à l'écran (après --scroll)
//   --hover N            survole la Nième ligne (1 = première)
//   --width W --height H taille de la fenêtre (1440 x 900)
//   --full               capture de la page entière (limitée à 6000 px)
//   --out fichier.png    sortie (tools/preview/shots/<theme>-<list>.png)
import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const theme = args[0];
const opt = (name, def) => {
    const i = args.indexOf('--' + name);
    return i === -1 ? def : args[i + 1];
};
const list = opt('list', 'anime');
const status = opt('status', null);
const width = Number(opt('width', 1440));
const height = Number(opt('height', 900));
const scroll = Number(opt('scroll', 0));
const hover = opt('hover', null);
const row = opt('row', null);
const full = args.includes('--full');
const out = opt('out', join(here, 'shots', `${theme.replace(/[\\/]/g, '_')}-${list}${status ? '-s' + status : ''}${hover ? '-h' + hover : ''}.png`));

const browser = await puppeteer.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
    args: ['--hide-scrollbars'],
});
try {
    const page = await browser.newPage();
    await page.setViewport({ width, height });
    if (status) {
        // MAL lit le statut dans l'URL ; la copie locale n'a que « all » : on simule l'onglet.
        await page.evaluateOnNewDocument((s) => {
            document.addEventListener('DOMContentLoaded', () => {
                document.body.dataset.query = JSON.stringify({ status: Number(s) });
                const names = { 7: 'all_anime', 1: 'watching', 2: 'completed', 3: 'onhold', 4: 'dropped', 6: 'plantowatch' };
                document.querySelectorAll('.status-button').forEach((b) => b.classList.remove('on'));
                const btn = document.querySelector('.status-button.' + names[s]) ||
                    document.querySelectorAll('.status-button')[[7, 1, 2, 3, 4, 6].indexOf(Number(s))];
                btn && btn.classList.add('on');
            });
        }, status);
    }
    await page.goto(`http://localhost:8765/tools/preview/cache/${list}.html?t=${theme}`, { waitUntil: 'networkidle2', timeout: 60000 });
    await page.evaluate(() => document.fonts.ready);
    await new Promise((r) => setTimeout(r, 1200));
    if (scroll) {
        await page.evaluate((y) => window.scrollTo(0, y), scroll);
        await new Promise((r) => setTimeout(r, 600));
    }
    if (row) {
        await page.evaluate((n) => document.querySelectorAll('tbody.list-item')[n - 1]?.scrollIntoView({ block: 'center' }), Number(row));
        await new Promise((r) => setTimeout(r, 600));
    }
    if (hover) {
        const rows = await page.$$('tbody.list-item');
        const row = rows[Number(hover) - 1];
        if (row) {
            await row.hover();
            await new Promise((r) => setTimeout(r, 900));
        }
    }
    mkdirSync(dirname(out), { recursive: true });
    if (full) {
        const h = await page.evaluate(() => Math.min(document.documentElement.scrollHeight, 6000));
        await page.setViewport({ width, height: h });
        await new Promise((r) => setTimeout(r, 800));
    }
    await page.screenshot({ path: out });
    console.log(out);
} finally {
    await browser.close();
}
