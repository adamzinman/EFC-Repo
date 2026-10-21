# Proposed project-library script: efc.ui  (ignition/script-python/efc/ui/code.py)
# Ignition 8.1 (Jython 2.7), 8.3 compatible. Embedded-view strategy (decision 24):
# the screen shell's right region is an Embedded View whose props.path and props.params
# are bound to session.custom.efcDw[<pageId>]; these functions only write that value.
# Graph expand (decision 26) is local to each dynamic-window view (custom.trendExpanded); it never
# changes the region width, so it is not handled here.
# Views call them from one-line event scripts:
#   symbol onClick:        efc.ui.openDynamic(self)
#   symbol onDoubleClick:  efc.ui.dblCmd(self)
#   window close button:   efc.ui.closeDynamic(self)
#   screen view onStartup: efc.ui.setDefaultDock(self, self.view.params.defaultDock)

# Dynamic-window id -> view path. Ids keep the dw_ names used in the templates' dockId param.
WINDOWS = {
    'dw_ValveDiscrete': 'Docks/ValveDiscrete', 'dw_ValveAnalog': 'Docks/ValveAnalog',
    'dw_Rotating': 'Docks/Rotating', 'dw_VFD': 'Docks/VFD', 'dw_Heater': 'Docks/Heater',
    'dw_HeatTransfer': 'Docks/HeatTransfer', 'dw_ProcessValue': 'Docks/ProcessValue',
    'dw_Loop': 'Docks/Loop', 'dw_Station': 'Docks/Station', 'dw_IOCard': 'Docks/IOCard',
}

# Two-state devices that accept a double-tap command: type -> (state member, cmd if on, cmd if off)
DBL_CMD = {
    'T_DValve': ('Sts_Opened', 'Cmd_Close', 'Cmd_Open'),
    'T_Motor':  ('Sts_Running', 'Cmd_Stop', 'Cmd_Start'),
}
READY_TRUE = ['Mode/Sts_Man', 'Sts_Avail']
READY_FALSE = ['Sts_Intlk', 'Sts_NotPerm', 'Sts_Local', 'Sts_Fault']


def _state(component):
    """This page's dynamic-window state: {'path', 'params', 'default'}."""
    s = component.session.custom
    if getattr(s, 'efcDw', None) is None:
        s.efcDw = {}
    pid = component.page.props.pageId
    st = dict(s.efcDw.get(pid) or {})
    return s, pid, st


def _write(component, **changes):
    s, pid, st = _state(component)
    st.update(changes)
    d = dict(s.efcDw)
    d[pid] = st
    s.efcDw = d


def openDynamic(component):
    """Single click on a template's symbol: show its dynamic window for this tag."""
    p = component.view.params
    _write(component, path=WINDOWS[p.dockId], params={'tagPath': p.tagPath})


def setDefaultDock(component, viewPath, params=None):
    """Screen onStartup: remember and show the screen's default right-region view."""
    if viewPath:
        _write(component, default={'path': viewPath, 'params': params or {}}, path=viewPath, params=params or {})


def closeDynamic(component):
    """Dynamic-window close button: return the right region to the screen's default view."""
    s, pid, st = _state(component)
    d = st.get('default') or {}
    _write(component, path=d.get('path'), params=d.get('params', {}))


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
