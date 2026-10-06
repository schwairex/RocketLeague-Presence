"""Restore native sizing for the Windows frameless pywebview window.

Subclass on the WinForms UI thread, retain the callback until WM_NCDESTROY,
and delegate all unrelated messages to the existing window procedure.
"""
import logging
import os

log = logging.getLogger(__name__)


def resize_hit_test(x, y, rect, border=8, maximized=False):
    left, top, right, bottom = rect
    if maximized or not (left <= x < right and top <= y < bottom):
        return 1  # HTCLIENT
    horizontal = 10 if x < left + border else 11 if x >= right - border else 0
    if y < top + border:
        return {10: 13, 11: 14}.get(horizontal, 12)
    if y >= bottom - border:
        return {10: 16, 11: 17}.get(horizontal, 15)
    return horizontal or 1


class NativeResize:
    def __init__(self, native, min_size):
        import ctypes as c
        from ctypes import wintypes as w
        self.native, self.min_size = native, min_size
        self.hwnd = native.Handle.ToInt64()
        self.user = c.WinDLL('user32', use_last_error=True)
        self.common = c.WinDLL('comctl32', use_last_error=True)
        self.callback_type = c.WINFUNCTYPE(c.c_ssize_t, w.HWND, w.UINT,
            c.c_size_t, c.c_ssize_t, c.c_size_t, c.c_size_t)
        self.common.SetWindowSubclass.argtypes = [w.HWND, self.callback_type, c.c_size_t, c.c_size_t]
        self.common.SetWindowSubclass.restype = w.BOOL
        self.common.RemoveWindowSubclass.argtypes = [w.HWND, self.callback_type, c.c_size_t]
        self.common.DefSubclassProc.argtypes = [w.HWND, w.UINT, c.c_size_t, c.c_ssize_t]
        self.common.DefSubclassProc.restype = c.c_ssize_t
        self.user.GetWindowRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
        self.user.IsZoomed.argtypes = [w.HWND]
        self.user.GetDpiForWindow.argtypes = [w.HWND]
        self.user.SetWindowPos.argtypes = [w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT]
        self.user.MonitorFromWindow.argtypes = [w.HWND,w.DWORD]
        self.user.MonitorFromWindow.restype = w.HANDLE
        self.user.GetMonitorInfoW.argtypes = [w.HANDLE,c.c_void_p]
        pointer64 = c.sizeof(c.c_void_p) == 8
        self.get_style = getattr(self.user,'GetWindowLongPtrW' if pointer64 else 'GetWindowLongW')
        self.set_style = getattr(self.user,'SetWindowLongPtrW' if pointer64 else 'SetWindowLongW')
        self.get_style.argtypes = [w.HWND,c.c_int]
        self.get_style.restype = c.c_ssize_t
        self.set_style.argtypes = [w.HWND,c.c_int,c.c_ssize_t]
        self.set_style.restype = c.c_ssize_t
        self.callback = self.callback_type(self._procedure)
        if not self.common.SetWindowSubclass(self.hwnd,self.callback,1,0):
            raise c.WinError(c.get_last_error())
        self.set_style(self.hwnd,-16,self.get_style(self.hwnd,-16) | 0x00040000 | 0x00010000)
        self.user.SetWindowPos(self.hwnd,None,0,0,0,0,0x0027)  # frame changed, no move/size/activate

    def _procedure(self, hwnd, message, wp, lp, subclass_id, data):
        import ctypes as c
        from ctypes import wintypes as w
        try:
            if message == 0x0083 and wp:  # WM_NCCALCSIZE: retain the existing custom titlebar
                return 0
            if message == 0x0084:  # WM_NCHITTEST, screen coordinates are signed
                rect = w.RECT()
                self.user.GetWindowRect(hwnd,c.byref(rect))
                x, y = c.c_short(lp & 0xffff).value, c.c_short((lp >> 16) & 0xffff).value
                border = max(6,round(8 * (self.user.GetDpiForWindow(hwnd) or 96)/96))
                hit = resize_hit_test(x,y,(rect.left,rect.top,rect.right,rect.bottom),border,self.user.IsZoomed(hwnd))
                if hit != 1:
                    return hit
            if message == 0x0024:  # WM_GETMINMAXINFO: avoid cropping when maximized
                result = self.common.DefSubclassProc(hwnd,message,wp,lp)
                class Limits(c.Structure):
                    _fields_ = [(name,w.POINT) for name in ('reserved','max_size','max_position','min_track','max_track')]
                class Monitor(c.Structure):
                    _fields_ = [('size',w.DWORD),('monitor',w.RECT),('work',w.RECT),('flags',w.DWORD)]
                limits = c.cast(lp,c.POINTER(Limits)).contents
                scale = (self.user.GetDpiForWindow(hwnd) or 96)/96
                limits.min_track.x, limits.min_track.y = [round(n*scale) for n in self.min_size]
                monitor = Monitor(); monitor.size = c.sizeof(Monitor)
                handle = self.user.MonitorFromWindow(hwnd,2)
                if self.user.GetMonitorInfoW(handle,c.byref(monitor)):
                    limits.max_position.x = monitor.work.left-monitor.monitor.left
                    limits.max_position.y = monitor.work.top-monitor.monitor.top
                    limits.max_size.x = monitor.work.right-monitor.work.left
                    limits.max_size.y = monitor.work.bottom-monitor.work.top
                return result
            if message == 0x0082:  # WM_NCDESTROY
                self.common.RemoveWindowSubclass(hwnd,self.callback,subclass_id)
        except Exception:
            log.exception('Native resize message failed')
        return self.common.DefSubclassProc(hwnd,message,wp,lp)


def enable_native_resize(window):
    if os.name != 'nt':
        return None
    from System import Action
    result = []
    def install():
        result.append(NativeResize(window.native,window.min_size))
    window.native.Invoke(Action(install))
    return result[0]
