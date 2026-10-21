# Proposed project-library script: efc.ui  (ignition/script-python/efc/ui/code.py)
# Ignition 8.1 (Jython 2.7), 8.3 compatible. Views call it from one-line event scripts:
#   symbol onClick:        efc.ui.openDynamic(self)
#   symbol onDoubleClick:  efc.ui.dblCmd(self)
#   dock close button:     efc.ui.closeDynamic(self)
#   screen view onStartup: efc.ui.setDefaultDock(self, self.view.params.defaultDock)

# Every library dynamic window. All are right-side docks configured in the HMI project's
# page configuration; only one is open at a time.
DOCKS = ['dw_ValveDiscrete', 'dw_ValveAnalog', 'dw_Rotating', 'dw_VFD', 'dw_HeatTransfer', 'dw_Heater',
         'dw_ProcessValue', 'dw_Loop', 'dw_Station', 'dw_IOCard']

# Two-state devices that accept a double-tap command: type -> (state member, cmd if on, cmd if off)
DBL_CMD = {
    'T_DValve': ('Sts_Opened', 'Cmd_Close', 'Cmd_Open'),
    'T_Motor':  ('Sts_Running', 'Cmd_Stop', 'Cmd_Start'),
}
# All must be true / false for a double-tap command to be sent.
READY_TRUE = ['Mode/Sts_Man', 'Sts_Avail']
READY_FALSE = ['Sts_Intlk', 'Sts_NotPerm', 'Sts_Local', 'Sts_Fault']


def _store(session):
    if not hasattr(session.custom, 'efcDefaultDock') or session.custom.efcDefaultDock is None:
        session.custom.efcDefaultDock = {}
    return session.custom.efcDefaultDock


def _open(component, dockId, params=None):
    for d in DOCKS:
        if d != dockId:
            system.perspective.closeDock(d)
    system.perspective.openDock(dockId, params=params or {})


def openDynamic(component):
    """Single click on a template's symbol: open its dynamic window for this tag."""
    p = component.view.params
    _open(component, p.dockId, {'tagPath': p.tagPath})


def setDefaultDock(component, dockId):
    """Screen onStartup: remember and open the screen's default right dock."""
    if not dockId:
        return
    _store(component.session)[component.page.props.pageId] = dockId
    _open(component, dockId)


def closeDynamic(component):
    """Dock close button: return the right dock to the screen's default view."""
    default = _store(component.session).get(component.page.props.pageId)
    if default:
        _open(component, default)
    else:
        for d in DOCKS:
            system.perspective.closeDock(d)


def dblCmd(component):
    """Double-click/tap on the symbol in touch mode: toggle a two-state device.
    Sent only when the template has useButton = false and dblCmd = true, the device is
    in Manual and available, and nothing blocks it."""
    p = component.view.params
    if p.useButton or not p.dblCmd or p.tType not in DBL_CMD:
        return
    base = p.tagPath
    state, cmdOn, cmdOff = DBL_CMD[p.tType]
    paths = [base + '/' + m for m in [state] + READY_TRUE + READY_FALSE]
    v = [q.value for q in system.tag.readBlocking(paths)]
    isOn, ready = v[0], v[1:1 + len(READY_TRUE)]
    blocked = v[1 + len(READY_TRUE):]
    if not all(ready) or any(blocked):
        return
    system.tag.writeBlocking([base + '/' + (cmdOn if isOn else cmdOff)], [True])
