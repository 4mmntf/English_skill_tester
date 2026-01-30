"""Type stubs for flet package"""
from typing import Any

class Page:
    def __init__(self) -> None: ...
    def add(self, *controls: Any) -> None: ...
    def update(self) -> None: ...
    def clean(self) -> None: ...
    title: str
    window_full_screen: bool
    window_min_width: int
    window_min_height: int
    theme_mode: Any
    bgcolor: Any
    overlay: list[Any]
    test_items: list[Any]

class Text:
    def __init__(
        self,
        value: str = "",
        size: int | None = None,
        color: Any | None = None,
        text_align: Any | None = None,
        weight: Any | None = None,
    ) -> None: ...
    value: str
    visible: bool
    color: Any

class ElevatedButton:
    def __init__(
        self,
        text: str = "",
        on_click: Any | None = None,
        width: int | None = None,
        height: int | None = None,
        bgcolor: Any | None = None,
        color: Any | None = None,
        disabled: bool = False,
        visible: bool = True,
    ) -> None: ...
    text: str
    disabled: bool
    visible: bool

class LineChart:
    def __init__(
        self,
        data_series: list[Any] | None = None,
        border: Any | None = None,
        left_axis: Any | None = None,
        bottom_axis: Any | None = None,
        tooltip_bgcolor: Any | None = None,
        min_y: float | None = None,
        max_y: float | None = None,
        min_x: int | None = None,
        max_x: int | None = None,
        height: int | None = None,
        width: int | None = None,
    ) -> None: ...
    data_series: list[Any]
    max_x: int

class LineChartData:
    def __init__(
        self,
        data_points: list[Any] | None = None,
        stroke_width: int | None = None,
        color: Any | None = None,
        below_line_bgcolor: Any | None = None,
    ) -> None: ...
    data_points: list[Any]

class LineChartDataPoint:
    def __init__(self, x: float, y: float) -> None: ...

class Container:
    def __init__(
        self,
        content: Any | None = None,
        padding: int | Any | None = None,
        bgcolor: Any | None = None,
        border: Any | None = None,
        border_radius: int | None = None,
        alignment: Any | None = None,
        right: int | float | None = None,
        top: int | float | None = None,
        bottom: int | float | None = None,
        left: int | float | None = None,
        expand: bool = False,
        width: int | float | None = None,
        height: int | float | None = None,
    ) -> None: ...

class Column:
    def __init__(
        self,
        controls: list[Any] | None = None,
        horizontal_alignment: Any | None = None,
        alignment: Any | None = None,
        spacing: int | float | None = None,
        scroll: Any | None = None,
        expand: bool = False,
    ) -> None: ...

class Row:
    def __init__(
        self,
        controls: list[Any] | None = None,
        alignment: Any | None = None,
        spacing: int | float | None = None,
        expand: bool = False,
    ) -> None: ...

class Stack:
    def __init__(
        self,
        controls: list[Any] | None = None,
        expand: bool = False,
    ) -> None: ...

class Tabs:
    def __init__(
        self,
        tabs: list[Any] | None = None,
        selected_index: int | None = None,
        on_change: Any | None = None,
        expand: bool = False,
        unselected_label_color: Any | None = None,
    ) -> None: ...
    tabs: list[Any]
    selected_index: int | None
    unselected_label_color: Any

class Tab:
    def __init__(
        self,
        text: str = "",
        content: Any | None = None,
    ) -> None: ...

class Dropdown:
    def __init__(
        self,
        label: str = "",
        options: list[Any] | None = None,
        value: str | None = None,
        width: int | None = None,
        disabled: bool = False,
        on_change: Any | None = None,
    ) -> None: ...
    value: str | None
    visible: bool

class Image:
    def __init__(
        self,
        src: str = "",
        width: int | None = None,
        height: int | None = None,
        fit: Any | None = None,
    ) -> None: ...
    visible: bool

class FilePicker:
    def __init__(
        self,
        on_result: Any | None = None,
    ) -> None: ...
    def get_directory_path(self) -> None: ...
    def pick_files(self, dialog_title: str | None = None, allowed_extensions: list[str] | None = None) -> None: ...

class FilePickerResultEvent:
    path: str | None

class ControlEvent:
    pass

class Colors:
    BLACK: Any
    WHITE: Any
    BLUE: Any
    GREEN: Any
    RED: Any
    ORANGE: Any
    GREY_400: Any
    GREY_700: Any
    BLUE_400: Any
    ORANGE_400: Any
    RED_400: Any
    BLUE_100: Any
    GREEN_100: Any
    PURPLE_100: Any
    ORANGE_100: Any
    RED_100: Any
    BLUE_GREY: Any
    ON_SURFACE: Any
    PURPLE: Any
    PURPLE_400: Any
    
    @staticmethod
    def with_opacity(opacity: float, color: Any) -> Any: ...

def with_opacity(opacity: float, color: Any) -> Any: ...

class TextAlign:
    CENTER: Any
    LEFT: Any

class FontWeight:
    BOLD: Any

class ImageFit:
    CONTAIN: Any

class ScrollMode:
    AUTO: Any

class MainAxisAlignment:
    CENTER: Any
    START: Any

class CrossAxisAlignment:
    CENTER: Any
    START: Any

class ThemeMode:
    LIGHT: Any

class AppView:
    FLET_APP: Any

class ChartAxis:
    def __init__(self, labels_size: int | None = None) -> None: ...

class Border:
    def __init__(
        self,
        bottom: Any | None = None,
        left: Any | None = None,
        top: Any | None = None,
        right: Any | None = None,
    ) -> None: ...

class BorderSide:
    def __init__(self, width: int, color: Any) -> None: ...

class alignment:
    @staticmethod
    def center() -> Any: ...

class border:
    @staticmethod
    def all(width: int, color: Any) -> Any: ...
    Border: type[Any]

class dropdown:
    class Option:
        def __init__(self, key: str, text: str) -> None: ...

def app(target: Any, view: Any | None = None) -> None: ...
