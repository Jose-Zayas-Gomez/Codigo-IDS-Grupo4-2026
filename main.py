import json
import math
import os
import sys
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from hardware_info import get_hardware_info


def make_label(text, object_name=None, alignment=Qt.AlignLeft):
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    label.setAlignment(alignment | Qt.AlignVCenter)
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    return label


def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    data = {
        "default_user": "nacha",
        "users": [
            {
                "username": "nacha",
                "display_name": "Nacha",
                "role": "Administrador",
                "profile_photo": "img/nacha.png",
                "password": "lolman12",
            },
            {
                "username": "maxine",
                "display_name": "Maxine",
                "role": "Usuario",
                "profile_photo": "img/maxine.jpg",
                "password": "123456",
            },
        ],
    }

    if not os.path.isfile(config_path):
        return data

    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return data

    users = []
    raw_users = config.get("users")
    if isinstance(raw_users, list):
        for entry in raw_users:
            if not isinstance(entry, dict):
                continue
            username = entry.get("username", "").strip()
            if not username:
                continue
            users.append(
                {
                    "username": username,
                    "display_name": entry.get("display_name", username).strip() or username,
                    "role": entry.get("role", "Usuario").strip() or "Usuario",
                    "profile_photo": entry.get("profile_photo", "").strip(),
                    "password": entry.get("password", ""),
                }
            )
    else:
        legacy_name = str(config.get("user_name", "")).strip()
        legacy_role = str(config.get("user_role", "")).strip() or "Usuario"
        legacy_photo = str(config.get("profile_photo", "")).strip()
        if legacy_name:
            users.append(
                {
                    "username": legacy_name.lower(),
                    "display_name": legacy_name,
                    "role": legacy_role,
                    "profile_photo": legacy_photo,
                    "password": "",
                }
            )

    if users:
        data["users"] = users

    default_user = str(config.get("default_user", "")).strip()
    if default_user:
        data["default_user"] = default_user

    return data


def normalize_username(value):
    return value.strip().lower()


def find_user_profile(config, username):
    key = normalize_username(username)
    for user in config.get("users", []):
        if normalize_username(user.get("username", "")) == key:
            return user
        if normalize_username(user.get("display_name", "")) == key:
            return user
    return None


def get_default_user(config):
    default_user = config.get("default_user", "")
    profile = find_user_profile(config, default_user)
    if profile:
        return profile
    users = config.get("users", [])
    return users[0] if users else {"display_name": "Usuario", "role": "", "profile_photo": ""}


def resolve_path(relative_path):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, relative_path))




def make_round_pixmap(image_path, size):
    pixmap = QPixmap(image_path)
    if pixmap.isNull():
        return None

    scaled = pixmap.scaled(
        size,
        size,
        Qt.KeepAspectRatioByExpanding,
        Qt.SmoothTransformation,
    )
    rounded = QPixmap(size, size)
    rounded.fill(Qt.transparent)

    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.Antialiasing)
    clip_path = QPainterPath()
    clip_path.addEllipse(0, 0, size, size)
    painter.setClipPath(clip_path)
    painter.drawPixmap(0, 0, scaled)
    painter.end()

    return rounded


def make_separator(object_name="separator"):
    line = QFrame()
    line.setObjectName(object_name)
    line.setFixedHeight(1)
    return line


def make_line_icon(size, color, draw_fn):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidth(2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    draw_fn(painter, size)
    painter.end()

    return pixmap


def make_text_icon(text, size, color):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor(color))
    painter.setFont(QFont("Segoe UI", int(size * 0.7), QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()

    return pixmap


def make_leaf_pixmap(size=18, color="#66bb22"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)

    path = QPainterPath()
    path.moveTo(size * 0.2, size * 0.6)
    path.quadTo(size * 0.45, size * 0.1, size * 0.85, size * 0.4)
    path.quadTo(size * 0.6, size * 0.9, size * 0.2, size * 0.6)
    painter.drawPath(path)

    painter.setPen(QPen(QColor("#0b0b0b"), 1))
    painter.drawLine(int(size * 0.35), int(size * 0.7), int(size * 0.7), int(size * 0.35))
    painter.end()

    return pixmap


def make_money_pixmap(size=18, color="#d89a1d"):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size - 1, size - 1)

    painter.setPen(QPen(QColor("#0b0b0b"), 1))
    painter.setFont(QFont("Segoe UI", int(size * 0.6), QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "$")
    painter.end()

    return pixmap


def make_home_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        roof = QPolygonF(
            [
                QPointF(side * 0.12, side * 0.6),
                QPointF(side * 0.5, side * 0.2),
                QPointF(side * 0.88, side * 0.6),
            ]
        )
        painter.drawPolyline(roof)
        painter.drawRect(QRectF(side * 0.22, side * 0.55, side * 0.56, side * 0.32))
        painter.drawRect(QRectF(side * 0.46, side * 0.68, side * 0.12, side * 0.19))

    return make_line_icon(size, color, draw)


def make_grid_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        cell = side * 0.26
        gap = side * 0.14
        start = side * 0.12
        for row in range(2):
            for col in range(2):
                x = start + col * (cell + gap)
                y = start + row * (cell + gap)
                painter.drawRect(QRectF(x, y, cell, cell))

    return make_line_icon(size, color, draw)


def make_bars_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        bar_width = side * 0.18
        gap = side * 0.1
        base = side * 0.78
        heights = [side * 0.3, side * 0.5, side * 0.68]
        for i, height in enumerate(heights):
            x = side * 0.18 + i * (bar_width + gap)
            painter.drawRoundedRect(
                QRectF(x, base - height, bar_width, height), 2, 2
            )

    return make_line_icon(size, color, draw)


def make_chip_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        painter.drawRect(QRectF(side * 0.25, side * 0.25, side * 0.5, side * 0.5))
        for i in range(3):
            offset = side * (0.3 + i * 0.2)
            painter.drawLine(QPointF(offset, side * 0.15), QPointF(offset, side * 0.25))
            painter.drawLine(
                QPointF(offset, side * 0.75), QPointF(offset, side * 0.85)
            )
            painter.drawLine(QPointF(side * 0.15, offset), QPointF(side * 0.25, offset))
            painter.drawLine(
                QPointF(side * 0.75, offset), QPointF(side * 0.85, offset)
            )

    return make_line_icon(size, color, draw)


def make_cloud_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        path = QPainterPath()
        path.moveTo(side * 0.22, side * 0.62)
        path.cubicTo(side * 0.18, side * 0.45, side * 0.32, side * 0.32, side * 0.46, side * 0.42)
        path.cubicTo(side * 0.5, side * 0.26, side * 0.74, side * 0.28, side * 0.74, side * 0.5)
        path.cubicTo(side * 0.86, side * 0.5, side * 0.86, side * 0.7, side * 0.72, side * 0.7)
        path.lineTo(side * 0.28, side * 0.7)
        path.cubicTo(side * 0.2, side * 0.7, side * 0.18, side * 0.64, side * 0.22, side * 0.62)
        painter.drawPath(path)

    return make_line_icon(size, color, draw)


def make_clock_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        painter.drawEllipse(QRectF(side * 0.18, side * 0.18, side * 0.64, side * 0.64))
        painter.drawLine(
            QPointF(side * 0.5, side * 0.5), QPointF(side * 0.5, side * 0.32)
        )
        painter.drawLine(
            QPointF(side * 0.5, side * 0.5), QPointF(side * 0.66, side * 0.56)
        )

    return make_line_icon(size, color, draw)


def make_gear_icon(size=18, color="#f2f2f2"):
    def draw(painter, side):
        center = QPointF(side * 0.5, side * 0.5)
        radius = side * 0.2
        painter.drawEllipse(center, radius, radius)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            start = QPointF(
                center.x() + math.cos(rad) * (radius + side * 0.02),
                center.y() + math.sin(rad) * (radius + side * 0.02),
            )
            end = QPointF(
                center.x() + math.cos(rad) * (radius + side * 0.12),
                center.y() + math.sin(rad) * (radius + side * 0.12),
            )
            painter.drawLine(start, end)

    return make_line_icon(size, color, draw)


def make_warning_icon(size=22, color="#f2f2f2"):
    def draw(painter, side):
        triangle = QPolygonF(
            [
                QPointF(side * 0.5, side * 0.12),
                QPointF(side * 0.1, side * 0.85),
                QPointF(side * 0.9, side * 0.85),
            ]
        )
        painter.drawPolygon(triangle)
        painter.drawLine(
            QPointF(side * 0.5, side * 0.35),
            QPointF(side * 0.5, side * 0.6),
        )
        painter.drawEllipse(QRectF(side * 0.46, side * 0.68, side * 0.08, side * 0.08))

    return make_line_icon(size, color, draw)


def make_exclamation_icon(size=22, color="#f2f2f2"):
    def draw(painter, side):
        painter.drawLine(
            QPointF(side * 0.5, side * 0.2),
            QPointF(side * 0.5, side * 0.65),
        )
        painter.drawEllipse(QRectF(side * 0.45, side * 0.73, side * 0.1, side * 0.1))

    return make_line_icon(size, color, draw)


def make_thumb_icon(size=22, color="#f2f2f2"):
    def draw(painter, side):
        path = QPainterPath()
        path.moveTo(side * 0.2, side * 0.55)
        path.lineTo(side * 0.45, side * 0.55)
        path.lineTo(side * 0.55, side * 0.32)
        path.lineTo(side * 0.72, side * 0.32)
        path.lineTo(side * 0.72, side * 0.75)
        path.lineTo(side * 0.2, side * 0.75)
        path.closeSubpath()
        painter.drawPath(path)

    return make_line_icon(size, color, draw)


def make_bulb_icon(size=22, color="#f2f2f2"):
    def draw(painter, side):
        painter.drawEllipse(QRectF(side * 0.26, side * 0.12, side * 0.48, side * 0.48))
        painter.drawLine(
            QPointF(side * 0.38, side * 0.66),
            QPointF(side * 0.62, side * 0.66),
        )
        painter.drawRect(QRectF(side * 0.4, side * 0.66, side * 0.2, side * 0.16))

    return make_line_icon(size, color, draw)


class MetricCard(QFrame):
    def __init__(
        self,
        title,
        icon_pixmap,
        value_text,
        percent_text,
        progress_value,
        progress_color,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setAttribute(Qt.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        title_label = make_label(title, "metricTitle")

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(QSize(22, 22))

        value_label = make_label(value_text, "metricValue")
        percent_label = make_label(percent_text, "metricPercent", alignment=Qt.AlignRight)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        top_row.addWidget(icon_label)
        top_row.addWidget(value_label, 1)
        top_row.addWidget(percent_label)

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(progress_value)
        progress.setTextVisible(False)
        progress.setFixedHeight(12)
        progress.setStyleSheet(
            "QProgressBar {"
            "  border: none;"
            "  background: #2a2a2a;"
            "  border-radius: 6px;"
            "}"
            "QProgressBar::chunk {"
            f"  background-color: {progress_color};"
            "  border-radius: 6px;"
            "}"
        )

        main_layout.addWidget(title_label)
        main_layout.addLayout(top_row)
        main_layout.addWidget(progress)


class SummaryCard(QFrame):
    def __init__(self, label_text, value_text, parent=None):
        super().__init__(parent)
        self.setObjectName("summaryCard")
        self.setAttribute(Qt.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        label = make_label(label_text, "summaryLabel")
        value = make_label(value_text, "summaryValue")

        layout.addWidget(label)
        layout.addWidget(value)


class PerformanceCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setObjectName("performanceCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        layout.addWidget(make_label(title, "performanceTitle"))
        layout.addStretch()

        value_label = make_label(value, "performanceValue")
        value_label.setWordWrap(True)
        layout.addWidget(value_label)


class DetailsPanel(QFrame):
    def __init__(self, title, rows, parent=None):
        super().__init__(parent)
        self.setObjectName("detailsPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.value_labels = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        layout.addWidget(make_label(title, "detailsTitle"))
        layout.addSpacing(4)

        for index, (label, value) in enumerate(rows):
            row = QHBoxLayout()
            row.setSpacing(12)
            row.addWidget(make_label(label, "detailLabel"))
            value_label = make_label(value, "detailValue", alignment=Qt.AlignRight)
            self.value_labels.append(value_label)
            row.addWidget(value_label)
            layout.addLayout(row)
            if index < len(rows) - 1:
                layout.addWidget(make_separator("detailLine"))

    def set_values(self, values):
        for label, value in zip(self.value_labels, values):
            label.setText(value)


class StatusCard(QFrame):
    def __init__(self, tone_color, icon_pixmap, title, description, parent=None):
        super().__init__(parent)
        self.setObjectName("statusCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        circle = QFrame()
        circle.setObjectName("statusCircle")
        circle.setFixedSize(88, 88)
        circle.setStyleSheet(
            "QFrame {"
            f"  background-color: {tone_color};"
            "  border-radius: 44px;"
            "}"
        )

        layout.addWidget(circle, 0, Qt.AlignHCenter)
        layout.addWidget(make_separator("statusDivider"))

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        icon_label = QLabel()
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(24, 24)

        title_label = make_label(title, "statusTitle")

        title_row.addWidget(icon_label)
        title_row.addWidget(title_label, 1)

        layout.addLayout(title_row)

        note = QFrame()
        note.setObjectName("statusNote")
        note_layout = QVBoxLayout(note)
        note_layout.setContentsMargins(12, 10, 12, 10)

        note_label = make_label(description, "statusNoteText")
        note_label.setWordWrap(True)
        note_layout.addWidget(note_label)

        layout.addWidget(note)


class InfoBar(QFrame):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setObjectName("infoBar")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        icon = QLabel()
        icon.setPixmap(make_bulb_icon(26))
        icon.setFixedSize(26, 26)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)

        title_label = make_label(title, "infoTitle")
        body_label = make_label(text, "infoText")
        body_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(body_label)

        layout.addWidget(icon)
        layout.addLayout(text_layout, 1)


class InfoCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        layout.addWidget(make_label(title, "infoCardTitle"))
        self.value_label = make_label(value, "infoCardValue")
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(value)


class ListPanel(QFrame):
    def __init__(self, title, items, parent=None):
        super().__init__(parent)
        self.setObjectName("listPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        layout.addWidget(make_label(title, "listTitle"))
        layout.addSpacing(4)

        for index, item in enumerate(items):
            item_label = make_label(item, "listItem")
            item_label.setWordWrap(True)
            layout.addWidget(item_label)
            if index < len(items) - 1:
                layout.addWidget(make_separator("listLine"))


class KpiCard(QFrame):
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        layout.addWidget(make_label(title, "kpiTitle"))
        layout.addStretch()
        layout.addWidget(make_label(value, "kpiValue"))


class ActivityPanel(QFrame):
    def __init__(
        self,
        items,
        title="Registro de Actividad",
        title_alignment=Qt.AlignLeft,
        object_name="activityPanel",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName(object_name)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title_label = make_label(title, "activityTitle", alignment=title_alignment)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addSpacing(4)

        for text in items:
            item_label = make_label(f"•  {text}", "activityItem")
            item_label.setWordWrap(True)
            layout.addWidget(item_label)


class HomeView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        header_icon = QLabel()
        header_icon.setPixmap(make_leaf_pixmap(22))
        header_icon.setFixedSize(QSize(22, 22))

        header_title = make_label("SEMÁFORO IA", "pageTitle")

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title, 1)

        layout.addLayout(header_layout)
        layout.addWidget(make_separator("separator"))

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(18)

        cards_layout.addWidget(
            StatusCard(
                "#b60f0f",
                make_warning_icon(22),
                "Huella de Carbono Alta",
                "Tu nivel de Huella de Carbono es alto. Se recomienda revisar el consumo energético y la configuración de hardware.",
            ),
            1,
        )
        cards_layout.addWidget(
            StatusCard(
                "#c4a600",
                make_exclamation_icon(22),
                "Huella de Carbono Moderada",
                "Tu nivel de Huella de Carbono es estándar. Se mantiene estable, pero existen oportunidades de mejora.",
            ),
            1,
        )
        cards_layout.addWidget(
            StatusCard(
                "#4eb541",
                make_thumb_icon(22),
                "Huella de Carbono Baja",
                "Tu nivel de Huella de Carbono es bajo y se mantiene con muy poco uso adicional.",
            ),
            1,
        )

        info_bar = InfoBar(
            "¿Cómo se calcula?",
            "La Huella de Carbono se estima a partir del consumo energético, tipo de hardware, tiempo de procesamiento, región de ejecución y factores de emisión del proveedor de nube seleccionado.",
        )

        layout.addLayout(cards_layout)
        layout.addWidget(info_bar)


class EnvironmentalPerformanceView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(22)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        header_icon = QLabel()
        header_icon.setPixmap(make_leaf_pixmap(20))
        header_icon.setFixedSize(QSize(20, 20))

        header_title = make_label("Panel de Rendimiento Ambiental", "pageTitle")

        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_title, 1)

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(18)
        metrics_layout.addWidget(PerformanceCard("Emisiones CO₂", "142 gCO2eq"), 1)
        metrics_layout.addWidget(PerformanceCard("Consumo Energético", "3.8 kWh"), 1)
        metrics_layout.addWidget(PerformanceCard("Tiempo de Procesamiento", "00:47:00 mins"), 1)

        details_rows = [
            ("Hardware", "NVIDIA A100"),
            ("Proveedor Nube", "AWS US-East-1"),
            ("Factor de Emisión", "0.386 kg/kWh"),
            ("Región", "Norteamérica"),
            ("Última ejecución", "Hace 2 minutos"),
            ("Estado del cálculo", "Finalizado"),
        ]
        details_panel = DetailsPanel("Detalles del Cálculo", details_rows)

        activity_items = [
            "Cálculo Ambiental finalizado correctamente.",
            "Métricas gCO2eq y kWh actualizadas en interfaz.",
            "Variables aún no inicializadas -- mostrando aviso de cálculo en curso",
            "Sesión iniciada. Hardware detectado.",
            "Excepción 1: datos no disponibles al iniciar.",
        ]
        activity_panel = ActivityPanel(activity_items, title_alignment=Qt.AlignLeft)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(18)
        bottom_row.addWidget(details_panel, 1)
        bottom_row.addWidget(activity_panel, 1)

        main_layout.addLayout(header_layout)
        main_layout.addWidget(make_separator("separator"))
        main_layout.addLayout(metrics_layout)
        main_layout.addLayout(bottom_row)


class CarbonDetailView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Comparativas", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        panel = QFrame()
        panel.setObjectName("detailModal")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(32, 28, 32, 28)
        panel_layout.setSpacing(14)

        icon = QLabel()
        icon.setPixmap(make_warning_icon(36))
        icon.setFixedSize(36, 36)

        title = make_label("Huella de Carbono Moderada", "modalTitle", alignment=Qt.AlignCenter)
        body = make_label(
            "Tu nivel de huella de carbono se encuentra en un rango de advertencia. "
            "Si bien el sistema opera dentro de márgenes aceptables, se han detectado "
            "parámetros que incrementan innecesariamente las emisiones de CO2 y el consumo energético. "
            "Es recomendable tomar acción antes de que el nivel escale a rango crítico.",
            "modalBody",
        )
        body.setWordWrap(True)

        bullet_1 = QLabel(
            "• <b>Región de ejecución:</b> Migrar las cargas de trabajo a regiones con menor factor de emisión, "
            "como Europa del Norte o Canada Central, puede reducir significativamente las emisiones sin afectar "
            "el rendimiento."
        )
        bullet_2 = QLabel(
            "• <b>Tiempo de procesamiento:</b> Optimizar los hiperparámetros del modelo o aplicar técnicas de early "
            "stopping puede disminuir el tiempo de cómputo y, con ello, el consumo energético asociado."
        )
        bullet_3 = QLabel(
            "• <b>Hardware:</b> Considerar el uso de aceleradores más eficientes energéticamente o ajustar la asignación "
            "de recursos para evitar capacidad ociosa durante la ejecución."
        )
        for bullet in (bullet_1, bullet_2, bullet_3):
            bullet.setObjectName("modalBullet")
            bullet.setWordWrap(True)
            bullet.setTextFormat(Qt.RichText)

        footer = make_label(
            "Implementar al menos una de estas medidas debería ser suficiente para retornar al rango verde en la próxima evaluación.",
            "modalBody",
        )
        footer.setWordWrap(True)

        button = QPushButton("Continuar")
        button.setObjectName("primaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedWidth(160)

        panel_layout.addWidget(icon, 0, Qt.AlignHCenter)
        panel_layout.addWidget(title)
        panel_layout.addWidget(body)
        panel_layout.addWidget(bullet_1)
        panel_layout.addWidget(bullet_2)
        panel_layout.addWidget(bullet_3)
        panel_layout.addWidget(footer)
        panel_layout.addWidget(button, 0, Qt.AlignHCenter)

        layout.addWidget(panel, 1)


class ModelsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Modelos", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(InfoCard("Modelos activos", "14"), 1)
        cards.addWidget(InfoCard("Latencia media", "128 ms"), 1)
        cards.addWidget(InfoCard("Precisión promedio", "92%"), 1)

        items = [
            "Llama 3 70B — Producción (GPU)",
            "Mistral Large — Validación (CPU)",
            "Gemma 27B — Sandbox (GPU)",
            "Phi-4 Mini — Batch (CPU)",
        ]
        list_panel = ListPanel("Modelos recientes", items)

        layout.addLayout(cards)
        layout.addWidget(list_panel)


class FinOpsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Costos FinOps", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(InfoCard("Costo actual", "$4.820.000"), 1)
        cards.addWidget(InfoCard("Presupuesto mensual", "$7.500.000"), 1)
        cards.addWidget(InfoCard("Ahorro estimado", "$1.120.000"), 1)

        items = [
            "GPU compute — 48% del gasto",
            "Storage + snapshots — 22% del gasto",
            "Networking — 14% del gasto",
            "Servicios administrados — 16% del gasto",
        ]
        list_panel = ListPanel("Desglose por servicio", items)

        layout.addLayout(cards)
        layout.addWidget(list_panel)


class CloudView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Cloud", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        self.provider_card = InfoCard("Proveedor", "AWS")
        self.region_card = InfoCard("Región activa", "US-East-1")
        self.status_card = InfoCard("Estado", "Operativo")

        cards = QHBoxLayout()
        cards.setSpacing(18)
        cards.addWidget(self.provider_card, 1)
        cards.addWidget(self.region_card, 1)
        cards.addWidget(self.status_card, 1)

        selector_panel = QFrame()
        selector_panel.setObjectName("cloudPanel")
        selector_layout = QHBoxLayout(selector_panel)
        selector_layout.setContentsMargins(18, 16, 18, 16)
        selector_layout.setSpacing(16)

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("cloudSelect")
        self.provider_combo.addItems(["AWS", "Azure", "GCP"])
        self.provider_combo.setFixedHeight(40)

        self.tier_combo = QComboBox()
        self.tier_combo.setObjectName("cloudSelect")
        self.tier_combo.addItems(["Básico", "Profesional", "Enterprise"])
        self.tier_combo.setFixedHeight(40)

        self.region_combo = QComboBox()
        self.region_combo.setObjectName("cloudSelect")
        self.region_combo.setFixedHeight(40)

        self.region_map = {
            "AWS": ["US-East-1", "US-West-2", "eu-north-1"],
            "Azure": ["East US", "West Europe", "South Central US"],
            "GCP": ["us-central1", "europe-west1", "southamerica-east1"],
        }

        selector_layout.addWidget(self._build_selector("Proveedor", self.provider_combo), 1)
        selector_layout.addWidget(self._build_selector("Tier", self.tier_combo), 1)
        selector_layout.addWidget(self._build_selector("Región", self.region_combo), 1)

        self.provider_combo.currentTextChanged.connect(self._update_regions)
        self.region_combo.currentTextChanged.connect(self._sync_cards)
        self._update_regions(self.provider_combo.currentText())

        items = [
            "GPU Instances: 6 activas",
            "Storage: 82 TB en uso",
            "Networking: 1.2 TB transferidos",
            "Backups: Última copia hace 3 horas",
        ]
        list_panel = ListPanel("Servicios activos", items)

        layout.addLayout(cards)
        layout.addWidget(selector_panel)
        layout.addWidget(list_panel)

    def _build_selector(self, label_text, combo):
        wrapper = QFrame()
        wrapper.setObjectName("cloudSelector")
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        layout.addWidget(make_label(label_text, "cloudLabel"))
        layout.addWidget(combo)
        return wrapper

    def _update_regions(self, provider):
        regions = self.region_map.get(provider, [])
        self.region_combo.clear()
        self.region_combo.addItems(regions)
        self._sync_cards()

    def _sync_cards(self):
        self.provider_card.set_value(self.provider_combo.currentText())
        self.region_card.set_value(self.region_combo.currentText())


class HistoryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Historial", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        items = [
            "Hace 3 min — Evaluación ambiental completada (GPU A100)",
            "Hace 1 h — Reporte de costos generado (FinOps)",
            "Hace 4 h — Validación de modelo Llama 3 70B",
            "Ayer — Rebalanceo de cargas a Europa del Norte",
        ]
        list_panel = ListPanel("Últimas ejecuciones", items)

        layout.addWidget(list_panel)


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        layout.addWidget(make_label("Ajustes", "pageTitle"))
        layout.addWidget(make_separator("separator"))

        items = [
            "Notificaciones: activas",
            "Modo de reporte: semanal",
            "Unidad de energía: kWh",
            "Idioma: Español",
        ]
        list_panel = ListPanel("Preferencias generales", items)

        layout.addWidget(list_panel)


class PatternPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("patternPanel")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0b0b0b"))
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(255, 255, 255, 28))
        pen.setWidth(1)
        painter.setPen(pen)

        size = 160
        half = size / 2
        width = self.width()
        height = self.height()

        for y in range(-size, height + size, size):
            for x in range(-size, width + size, size):
                diamond = QPolygonF(
                    [
                        QPointF(x, y - half),
                        QPointF(x + half, y),
                        QPointF(x, y + half),
                        QPointF(x - half, y),
                    ]
                )
                painter.drawPolygon(diamond)


class LoginUserCard(QFrame):
    def __init__(self, user_profile, parent=None):
        super().__init__(parent)
        self.setObjectName("loginUserCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        avatar = QLabel()
        photo_path = user_profile.get("profile_photo", "")
        avatar_pixmap = None
        if photo_path:
            avatar_pixmap = make_round_pixmap(resolve_path(photo_path), 34)
        if avatar_pixmap:
            avatar.setPixmap(avatar_pixmap)
        else:
            avatar.setText(user_profile.get("display_name", "?")[:1].upper())
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setObjectName("loginAvatarFallback")

        avatar.setFixedSize(34, 34)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.addWidget(make_label(user_profile.get("display_name", ""), "loginUserName"))
        text_layout.addWidget(make_label(user_profile.get("role", ""), "loginUserRole"))

        layout.addWidget(avatar)
        layout.addLayout(text_layout)
        layout.addStretch()


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.setWindowTitle("Semáforo IA - Login")
        self.resize(1100, 640)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        left_panel = PatternPanel()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(18)

        brand_icon = QLabel()
        brand_icon.setPixmap(make_leaf_pixmap(64))
        brand_icon.setFixedSize(64, 64)

        brand_title = make_label("SEMÁFORO\nIA", "loginBrand", alignment=Qt.AlignCenter)

        left_layout.addStretch()
        left_layout.addWidget(brand_icon, 0, Qt.AlignHCenter)
        left_layout.addWidget(brand_title, 0, Qt.AlignHCenter)
        left_layout.addStretch()

        right_panel = QFrame()
        right_panel.setObjectName("loginPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(48, 48, 48, 48)
        right_layout.setSpacing(16)

        right_layout.addWidget(make_label("Login", "loginCaption"))
        right_layout.addWidget(make_label("Bienvenido de Vuelta", "loginTitle"))
        right_layout.addSpacing(8)

        right_layout.addWidget(make_label("Usuario", "loginLabel"))
        self.username_input = QLineEdit()
        self.username_input.setObjectName("loginInput")
        self.username_input.setPlaceholderText("Ingrese un usuario")
        self.username_input.setFixedHeight(40)

        right_layout.addWidget(self.username_input)

        right_layout.addWidget(make_label("Contraseña", "loginLabel"))
        self.password_input = QLineEdit()
        self.password_input.setObjectName("loginInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("••••••••")
        self.password_input.setFixedHeight(40)

        right_layout.addWidget(self.password_input)

        self.error_label = make_label("", "loginError")
        self.error_label.setVisible(False)
        right_layout.addWidget(self.error_label)

        login_button = QPushButton("Continuar")
        login_button.setObjectName("loginButton")
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.setFixedWidth(140)
        login_button.clicked.connect(self.handle_login)

        right_layout.addWidget(login_button, 0, Qt.AlignLeft)
        right_layout.addSpacing(10)

        users_label = make_label("Usuarios disponibles", "loginHint")
        right_layout.addWidget(users_label)

        user_cards = QVBoxLayout()
        user_cards.setSpacing(8)
        for profile in self.config.get("users", []):
            user_cards.addWidget(LoginUserCard(profile))
        right_layout.addLayout(user_cards)

        right_layout.addStretch()

        root_layout.addWidget(left_panel, 3)
        root_layout.addWidget(right_panel, 2)

        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)

    def handle_login(self):
        username = self.username_input.text().strip()
        if not username:
            self._set_error("Ingresa un usuario válido.")
            return

        profile = find_user_profile(self.config, username)
        if not profile:
            self._set_error("Usuario no encontrado. Usa nacha o maxine.")
            return

        password = self.password_input.text()
        expected = str(profile.get("password", ""))
        if expected and password != expected:
            self._set_error("Contraseña incorrecta.")
            return

        self.error_label.setVisible(False)
        self.dashboard = DashboardWindow(profile)
        self.dashboard.show()
        self.close()

    def _set_error(self, message):
        self.error_label.setText(message)
        self.error_label.setVisible(True)


class CatalogRow(QFrame):
    def __init__(self, component, comp_type, vcpus, ram, tdp, parent=None):
        super().__init__(parent)
        self.setObjectName("catalogRow")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(10)

        layout.addWidget(make_label(component, "catalogCell"), 3)
        layout.addWidget(make_label(comp_type, "catalogCell", alignment=Qt.AlignCenter), 1)
        layout.addWidget(make_label(vcpus, "catalogCell", alignment=Qt.AlignCenter), 1)
        layout.addWidget(make_label(ram, "catalogCell", alignment=Qt.AlignCenter), 1)
        layout.addWidget(make_label(tdp, "catalogCell", alignment=Qt.AlignCenter), 1)

        assign_button = QPushButton("Asignar")
        assign_button.setObjectName("assignButton")
        assign_button.setFixedHeight(32)
        assign_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(assign_button, 1, alignment=Qt.AlignRight)


class HardwareCatalogView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._hardware_loaded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        title = make_label("Catálogo de Hardware", "pageTitle")

        placeholder = "Detectando..."
        hardware_rows = [
            ("CPU", placeholder),
            ("GPU", placeholder),
            ("RAM", placeholder),
            ("Sistema", placeholder),
        ]
        self.hardware_panel = DetailsPanel("Hardware detectado", hardware_rows)
        self.hardware_panel.setObjectName("hardwarePanel")

        catalog_panel = QFrame()
        catalog_panel.setObjectName("catalogPanel")
        panel_layout = QVBoxLayout(catalog_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(16)

        search_row = QHBoxLayout()
        search_row.setSpacing(16)

        search_input = QLineEdit()
        search_input.setObjectName("searchInput")
        search_input.setPlaceholderText("Buscar componente...")
        search_input.setFixedHeight(42)

        filter_combo = QComboBox()
        filter_combo.setObjectName("filterCombo")
        filter_combo.addItems(["TDP máx: todos", "TDP máx: 125W", "TDP máx: 225W", "TDP máx: 400W"])
        filter_combo.setFixedHeight(42)
        filter_combo.setMinimumWidth(220)

        search_row.addWidget(search_input, 3)
        search_row.addWidget(filter_combo, 1)

        header = QFrame()
        header.setObjectName("catalogHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 10, 18, 10)
        header_layout.setSpacing(10)

        header_layout.addWidget(make_label("Componente", "catalogHeaderLabel"), 3)
        header_layout.addWidget(make_label("Tipo", "catalogHeaderLabel", alignment=Qt.AlignCenter), 1)
        header_layout.addWidget(make_label("vCPUs", "catalogHeaderLabel", alignment=Qt.AlignCenter), 1)
        header_layout.addWidget(make_label("RAM", "catalogHeaderLabel", alignment=Qt.AlignCenter), 1)
        header_layout.addWidget(make_label("TDP", "catalogHeaderLabel", alignment=Qt.AlignCenter), 1)
        header_layout.addWidget(make_label("", "catalogHeaderLabel"), 1)

        rows = QVBoxLayout()
        rows.setSpacing(0)
        rows.addWidget(CatalogRow("Intel Xenon ES-2690", "CPU", "16", "--", "135W"))
        rows.addWidget(CatalogRow("AMD EPYC 7742", "CPU", "64", "--", "225W"))
        rows.addWidget(CatalogRow("NVIDIA A100 80GB", "GPU", "--", "80GB", "400W"))
        rows.addWidget(CatalogRow("Intel Core i9-13900k", "CPU", "24", "--", "125W"))

        panel_layout.addLayout(search_row)
        panel_layout.addWidget(header)
        panel_layout.addLayout(rows)

        layout.addWidget(title)
        layout.addWidget(make_separator("separator"))
        layout.addWidget(self.hardware_panel)
        layout.addWidget(catalog_panel)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._hardware_loaded:
            self._hardware_loaded = True
            QTimer.singleShot(50, self._load_hardware)

    def _load_hardware(self):
        info = get_hardware_info()
        values = [
            info.get("cpu", "No detectado"),
            info.get("gpu", "No detectado"),
            info.get("ram", "No detectado"),
            info.get("os", "No detectado"),
        ]
        self.hardware_panel.set_values(values)


class PlaceholderView(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(make_label(title, "pageTitle"))
        layout.addWidget(make_separator("separator"))
        layout.addWidget(make_label("Vista en construcción", "placeholderText"))


class Sidebar(QFrame):
    def __init__(self, user_profile, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.user_profile = user_profile

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(18)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        brand_icon = QLabel()
        brand_icon.setPixmap(make_leaf_pixmap(26))
        brand_icon.setFixedSize(QSize(26, 26))

        brand_title = make_label("SEMÁFORO IA", "brandTitle")

        brand_row.addWidget(brand_icon)
        brand_row.addWidget(brand_title)
        brand_row.addStretch()

        self.nav_layout = QVBoxLayout()
        self.nav_layout.setSpacing(6)

        layout.addLayout(brand_row)
        layout.addLayout(self.nav_layout)
        layout.addStretch()
        layout.addWidget(self._build_user_card())

    def add_nav_button(self, text, icon_pixmap):
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.setIcon(QIcon(icon_pixmap))
        button.setIconSize(QSize(18, 18))
        button.setCheckable(True)
        button.setCursor(Qt.PointingHandCursor)

        self.button_group.addButton(button)
        self.nav_layout.addWidget(button)
        return button

    def _build_user_card(self):
        card = QFrame()
        card.setObjectName("userCard")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        user_name = self.user_profile.get("display_name", "Usuario")
        user_role = self.user_profile.get("role", "")
        photo_path = self.user_profile.get("profile_photo", "")

        avatar_pixmap = None
        if photo_path:
            resolved = resolve_path(photo_path)
            avatar_pixmap = make_round_pixmap(resolved, 42)

        if avatar_pixmap:
            avatar = QLabel()
            avatar.setObjectName("userAvatar")
            avatar.setPixmap(avatar_pixmap)
        else:
            initial = user_name[:1].upper() if user_name else "?"
            avatar = QLabel(initial)
            avatar.setObjectName("userInitial")
            avatar.setAlignment(Qt.AlignCenter)

        avatar.setFixedSize(42, 42)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.addWidget(make_label(user_name, "userName"))
        info_layout.addWidget(make_label(user_role, "userRole"))

        chevron = QLabel("v")
        chevron.setObjectName("userChevron")
        chevron.setAlignment(Qt.AlignCenter)
        chevron.setFixedWidth(16)

        layout.addWidget(avatar)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(chevron)

        return card


class DashboardWindow(QMainWindow):
    def __init__(self, user_profile=None):
        super().__init__()

        self.setWindowTitle("Semáforo IA")
        self.setWindowIcon(QIcon(make_leaf_pixmap(64)))
        self.resize(1200, 720)

        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        config = load_config()
        if user_profile is None:
            config = load_config()
            user_profile = get_default_user(config)

        sidebar = Sidebar(user_profile)
        self.stack = QStackedWidget()

        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.addWidget(self.stack)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content_frame, 1)

        self._add_nav_item(sidebar, "Inicio", make_home_icon(), HomeView())
        self._add_nav_item(sidebar, "Modelos", make_grid_icon(), ModelsView())
        self._add_nav_item(
            sidebar,
            "Impacto Ambiental",
            make_leaf_pixmap(18, "#66bb22"),
            EnvironmentalPerformanceView(),
        )
        self._add_nav_item(
            sidebar,
            "Costos FinOps",
            make_text_icon("$", 18, "#66bb22"),
            FinOpsView(),
        )
        self._add_nav_item(sidebar, "Comparativas", make_bars_icon(), CarbonDetailView())
        self._add_nav_item(sidebar, "Hardware", make_chip_icon(), HardwareCatalogView())
        self._add_nav_item(sidebar, "Cloud", make_cloud_icon(), CloudView())
        self._add_nav_item(sidebar, "Historial", make_clock_icon(), HistoryView())
        self._add_nav_item(sidebar, "Ajustes", make_gear_icon(), SettingsView())

        sidebar.button_group.buttons()[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _add_nav_item(self, sidebar, label, icon, widget):
        button = sidebar.add_nav_button(label, icon)
        index = self.stack.addWidget(widget)
        button.clicked.connect(lambda checked=False, idx=index: self.stack.setCurrentIndex(idx))
        return button


def apply_stylesheet(app):
    app.setStyleSheet(
        "QWidget {"
        "  background-color: #0b0b0b;"
        "  color: #f4f4f4;"
        "  font-family: 'Segoe UI';"
        "}"
        "QLabel {"
        "  background: transparent;"
        "}"
        "QLineEdit {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 10px;"
        "  padding: 8px 12px;"
        "  font-size: 13px;"
        "}"
        "QLineEdit:focus {"
        "  border: 1px solid #ffffff;"
        "}"
        "QFrame#sidebar {"
        "  background-color: #0f0f0f;"
        "  border-right: 1px solid #1e1e1e;"
        "}"
        "QLabel#brandTitle {"
        "  font-size: 18px;"
        "  font-weight: 700;"
        "  letter-spacing: 0.6px;"
        "}"
        "QPushButton#navButton {"
        "  background: transparent;"
        "  border: none;"
        "  color: #e6e6e6;"
        "  padding: 10px 12px;"
        "  border-radius: 12px;"
        "  text-align: left;"
        "}"
        "QPushButton#navButton:hover {"
        "  background-color: #171717;"
        "}"
        "QPushButton#navButton:checked {"
        "  background-color: #2a3a17;"
        "  border: 1px solid #3a5220;"
        "  color: #ffffff;"
        "}"
        "QFrame#userCard {"
        "  background-color: #101010;"
        "  border: 1px solid #242424;"
        "  border-radius: 16px;"
        "}"
        "QLabel#userInitial {"
        "  background-color: #151515;"
        "  border: 1px solid #2a2a2a;"
        "  border-radius: 21px;"
        "  font-weight: 600;"
        "}"
        "QLabel#userAvatar {"
        "  border: 1px solid #2a2a2a;"
        "  border-radius: 21px;"
        "}"
        "QLabel#userName {"
        "  font-size: 13px;"
        "  font-weight: 600;"
        "}"
        "QLabel#userRole {"
        "  font-size: 11px;"
        "  color: #9a9a9a;"
        "}"
        "QLabel#userChevron {"
        "  color: #8a8a8a;"
        "  font-size: 12px;"
        "}"
        "QFrame#contentFrame {"
        "  background-color: #0b0b0b;"
        "}"
        "QFrame#loginPanel {"
        "  background-color: #0d0d0d;"
        "  border-left: 1px solid #1d1d1d;"
        "}"
        "QLabel#loginBrand {"
        "  font-size: 52px;"
        "  font-weight: 700;"
        "  letter-spacing: 2px;"
        "  font-family: 'Georgia';"
        "}"
        "QLabel#loginCaption {"
        "  font-size: 13px;"
        "  color: #cfcfcf;"
        "}"
        "QLabel#loginTitle {"
        "  font-size: 22px;"
        "  font-weight: 700;"
        "}"
        "QLabel#loginLabel {"
        "  font-size: 13px;"
        "  color: #d8d8d8;"
        "}"
        "QLabel#loginHint {"
        "  font-size: 12px;"
        "  color: #9a9a9a;"
        "}"
        "QLabel#loginError {"
        "  font-size: 12px;"
        "  color: #ff6b6b;"
        "}"
        "QLineEdit#loginInput {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 10px;"
        "  padding: 8px 12px;"
        "  font-size: 13px;"
        "}"
        "QPushButton#loginButton {"
        "  background-color: #0f0f0f;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 12px;"
        "  padding: 8px 16px;"
        "  font-weight: 600;"
        "}"
        "QPushButton#loginButton:hover {"
        "  background-color: #1a1a1a;"
        "}"
        "QFrame#loginUserCard {"
        "  background-color: #111111;"
        "  border: 1px solid #222222;"
        "  border-radius: 12px;"
        "}"
        "QLabel#loginUserName {"
        "  font-size: 12px;"
        "  font-weight: 600;"
        "}"
        "QLabel#loginUserRole {"
        "  font-size: 11px;"
        "  color: #9a9a9a;"
        "}"
        "QLabel#loginAvatarFallback {"
        "  background-color: #151515;"
        "  border: 1px solid #2a2a2a;"
        "  border-radius: 17px;"
        "}"
        "QFrame#metricCard, QFrame#summaryPanel, QFrame#summaryCard {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 18px;"
        "}"
        "QFrame#summaryPanel {"
        "  background-color: #111111;"
        "}"
        "QFrame#metricCard:hover, QFrame#summaryCard:hover {"
        "  background-color: #171717;"
        "  border: 1px solid #ffffff;"
        "}"
        "QFrame#kpiCard, QFrame#activityPanel, QFrame#catalogPanel {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 18px;"
        "}"
        "QFrame#performanceCard, QFrame#detailsPanel, QFrame#hardwarePanel, QFrame#statusCard, QFrame#infoBar, QFrame#infoCard, QFrame#listPanel, QFrame#cloudPanel {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 18px;"
        "}"
        "QFrame#cloudSelector {"
        "  background-color: transparent;"
        "}"
        "QFrame#activityPanel {"
        "  background-color: #121212;"
        "}"
        "QFrame#infoBar {"
        "  background-color: #101010;"
        "}"
        "QFrame#detailModal {"
        "  background-color: #111111;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 28px;"
        "}"
        "QFrame#statusNote {"
        "  background-color: #0f0f0f;"
        "  border: 1px solid #2a2a2a;"
        "  border-radius: 12px;"
        "}"
        "QFrame#catalogHeader {"
        "  background-color: #1b1b1b;"
        "  border: 1px solid #2c2c2c;"
        "  border-radius: 12px;"
        "}"
        "QFrame#catalogRow {"
        "  background-color: transparent;"
        "  border-bottom: 1px solid #2c2c2c;"
        "}"
        "QLabel#pageTitle {"
        "  font-size: 26px;"
        "  font-weight: 700;"
        "}"
        "QLabel#performanceTitle {"
        "  font-size: 13px;"
        "  color: #d6d6d6;"
        "}"
        "QLabel#performanceValue {"
        "  font-size: 28px;"
        "  font-weight: 700;"
        "}"
        "QLabel#detailsTitle {"
        "  font-size: 15px;"
        "  font-weight: 600;"
        "}"
        "QLabel#detailLabel {"
        "  font-size: 13px;"
        "  color: #cfcfcf;"
        "}"
        "QLabel#detailValue {"
        "  font-size: 13px;"
        "  font-weight: 600;"
        "}"
        "QLabel#statusTitle {"
        "  font-size: 14px;"
        "  font-weight: 600;"
        "}"
        "QLabel#statusNoteText {"
        "  font-size: 12px;"
        "  color: #d6d6d6;"
        "}"
        "QLabel#infoTitle {"
        "  font-size: 14px;"
        "  font-weight: 600;"
        "}"
        "QLabel#infoText {"
        "  font-size: 12px;"
        "  color: #d6d6d6;"
        "}"
        "QLabel#modalTitle {"
        "  font-size: 18px;"
        "  font-weight: 700;"
        "}"
        "QLabel#modalBody {"
        "  font-size: 13px;"
        "  color: #d6d6d6;"
        "}"
        "QLabel#modalBullet {"
        "  font-size: 13px;"
        "  color: #e6e6e6;"
        "}"
        "QLabel#infoCardTitle {"
        "  font-size: 12px;"
        "  color: #bfbfbf;"
        "  background: transparent;"
        "}"
        "QLabel#infoCardValue {"
        "  font-size: 18px;"
        "  font-weight: 700;"
        "  background: transparent;"
        "}"
        "QLabel#cloudLabel {"
        "  font-size: 12px;"
        "  color: #cfcfcf;"
        "  background: transparent;"
        "}"
        "QLabel#listTitle {"
        "  font-size: 15px;"
        "  font-weight: 600;"
        "}"
        "QLabel#listItem {"
        "  font-size: 13px;"
        "  color: #e0e0e0;"
        "}"
        "QLabel#placeholderText {"
        "  color: #8f8f8f;"
        "  font-size: 14px;"
        "}"
        "QLabel#titleLabel {"
        "  font-size: 26px;"
        "  font-weight: 700;"
        "}"
        "QLabel#sectionTitle {"
        "  font-size: 18px;"
        "  font-weight: 600;"
        "}"
        "QLabel#kpiTitle {"
        "  font-size: 14px;"
        "  color: #d0d0d0;"
        "}"
        "QLabel#kpiValue {"
        "  font-size: 28px;"
        "  font-weight: 700;"
        "}"
        "QLabel#activityTitle {"
        "  font-size: 20px;"
        "  font-weight: 700;"
        "}"
        "QLabel#activityItem {"
        "  font-size: 13px;"
        "  color: #d6d6d6;"
        "}"
        "QLabel#catalogHeaderLabel {"
        "  font-size: 13px;"
        "  font-weight: 600;"
        "  color: #f1f1f1;"
        "}"
        "QLabel#catalogCell {"
        "  font-size: 13px;"
        "  color: #ededed;"
        "}"
        "QLabel#metricTitle {"
        "  font-size: 13px;"
        "  color: #cfcfcf;"
        "  text-transform: uppercase;"
        "  letter-spacing: 0.6px;"
        "}"
        "QLabel#metricValue {"
        "  font-size: 18px;"
        "  font-weight: 600;"
        "}"
        "QLabel#metricPercent {"
        "  font-size: 16px;"
        "  font-weight: 600;"
        "  color: #f7f7f7;"
        "}"
        "QLabel#summaryLabel {"
        "  font-size: 13px;"
        "  color: #c2c2c2;"
        "}"
        "QLabel#summaryValue {"
        "  font-size: 20px;"
        "  font-weight: 700;"
        "}"
        "QFrame#separator, QFrame#contentLine, QFrame#detailLine, QFrame#listLine, QFrame#statusDivider {"
        "  background-color: #2a2a2a;"
        "}"
        "QLineEdit#searchInput {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 10px;"
        "  padding: 8px 14px;"
        "  font-size: 13px;"
        "}"
        "QLineEdit#searchInput::placeholder {"
        "  color: #7f7f7f;"
        "}"
        "QComboBox#filterCombo, QComboBox#cloudSelect {"
        "  background-color: #141414;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 10px;"
        "  padding: 6px 12px;"
        "  font-size: 13px;"
        "}"
        "QComboBox#filterCombo::drop-down, QComboBox#cloudSelect::drop-down {"
        "  border: none;"
        "  width: 20px;"
        "}"
        "QPushButton#assignButton {"
        "  background-color: #111111;"
        "  border: 1px solid #5a5a5a;"
        "  border-radius: 10px;"
        "  padding: 4px 14px;"
        "  color: #f1f1f1;"
        "}"
        "QPushButton#assignButton:hover {"
        "  background-color: #1a1a1a;"
        "  border: 1px solid #f0f0f0;"
        "}"
        "QPushButton#primaryButton {"
        "  background-color: #111111;"
        "  border: 1px solid #f2f2f2;"
        "  border-radius: 12px;"
        "  padding: 8px 20px;"
        "  font-weight: 600;"
        "}"
        "QPushButton#primaryButton:hover {"
        "  background-color: #1a1a1a;"
        "}"
    )


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    apply_stylesheet(app)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
