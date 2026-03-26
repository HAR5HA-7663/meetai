// KWin script: force MeetAI window to stay above all others
const clients = workspace.stackingOrder;
for (let i = 0; i < clients.length; i++) {
    const w = clients[i];
    if (w.caption === "MeetAI" || w.resourceClass === "python3" || w.resourceClass === "meetai") {
        w.keepAbove = true;
        w.skipTaskbar = true;
        w.skipPager = true;
        w.skipSwitcher = true;
    }
}

workspace.windowAdded.connect(function(w) {
    if (w.caption === "MeetAI") {
        w.keepAbove = true;
        w.skipTaskbar = true;
        w.skipPager = true;
        w.skipSwitcher = true;
    }
});
