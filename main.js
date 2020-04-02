const { app, BrowserWindow } = require('electron')

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
}

function createWindow(iter) {
    let win = new BrowserWindow({ width: 800, height: 1500 })
    win.maximize()
    const wc = win.webContents
    wc.openDevTools()

    wc.on('did-finish-load', async function() {
        await sleep(2000)
        for (let i = 0; i < iter; i++) {
            win.webContents.sendInputEvent({ type: 'keyDown', keyCode: 'PageDown' })
            win.webContents.sendInputEvent({ type: 'char', keyCode: 'PageDown' })
            win.webContents.sendInputEvent({ type: 'KeyUp', keyCode: 'PageDown' })
            await sleep(500)
        }
    });

    win.loadURL('https://books.google.de/books?id=zZluSj3AT6YC&lpg=PP1&pg=PP1#v=onepage&q&f=true')
}

app.whenReady().then(() => createWindow(475))
