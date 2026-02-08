# Сигналы, излучаемые приложением
from django import dispatch

# Сигнал о копировании связей с файлами
copy_file_links_signal = dispatch.Signal()

# Сигнал о копировании ролей разработчиков
copy_design_roles_signal = dispatch.Signal()

# Сигнал о создании основного маршрута
use_default_route_signal = dispatch.Signal()
