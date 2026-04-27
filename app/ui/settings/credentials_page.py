from PySide6 import QtWidgets, QtCore, QtGui
from ..dayu_widgets.label import MLabel
from ..dayu_widgets.line_edit import MLineEdit
from ..dayu_widgets.check_box import MCheckBox
from ..dayu_widgets.push_button import MPushButton
from ..dayu_widgets.line_tab_widget import MLineTabWidget
from ..dayu_widgets.message import MMessage
from ..dayu_widgets.loading import MLoadingWrapper
from .utils import set_label_width
from modules.translation.models import ModelManager
from app.account.auth.token_storage import get_token
import os
import requests

PROVIDER_ICONS = {
    "Google Gemini": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/gemini-color.svg",
    "OpenRouter": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/openrouter.svg",
    "9Router": "https://raw.githubusercontent.com/google/material-design-icons/master/symbols/web/hub/materialsymbolsoutlined/hub_24px.svg",
    "Ollama": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/ollama.svg",
    "Googletrans": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/google-color.svg",
    "DeeLX": "https://avatars.githubusercontent.com/u/82772671?s=200&v=4",
    "Custom": "local",
    "Deepseek": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/deepseek-color.svg",
    "Open AI GPT": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/openai.svg",
    "Microsoft Azure": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/azure-color.svg",
    "Google Cloud": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/googlecloud-color.svg",
    "DeepL": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/deepl-color.svg",
    "Anthropic Claude": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/claude-color.svg",
    "Yandex": "https://unpkg.com/@lobehub/icons-static-svg@1.88.0/icons/yandex.svg",
    "Comic Translate (Official)": "https://raw.githubusercontent.com/ogkalu2/comic-translate/refs/heads/main/resources/icons/icon.ico"
}

class IconFetchThread(QtCore.QThread):
    finished = QtCore.Signal(bytes)
    
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        
    def run(self):
        try:
            response = requests.get(self.url, timeout=5)
            if response.status_code == 200:
                self.finished.emit(response.content)
        except Exception:
            pass


class ProviderCard(QtWidgets.QFrame):
    clicked = QtCore.Signal()

    def __init__(self, service_label, parent=None):
        super().__init__(parent)
        self.service_label = service_label
        self.setFixedSize(180, 65)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setObjectName("ProviderCard")
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Icon
        self.icon_label = QtWidgets.QLabel()
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        if service_label == "9Router" or service_label == self.tr("9Router"):
            self.icon_label.setStyleSheet("""
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f97815, stop:1 #c2590a);
                border-radius: 8px;
            """)
        else:
            self.icon_label.setStyleSheet("background-color: transparent;")
        
        # Determine internal name to get correct icon mapping
        internal_name = service_label
        # (A bit of a hack to map names back if needed, but the labels generally match the dict)
        
        icon_url = PROVIDER_ICONS.get(service_label)
        
        if icon_url == "local":
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..'))
            icon_path = os.path.join(project_root, 'resources', 'static', 'settings.svg')
            if os.path.exists(icon_path):
                self._set_icon_pixmap(filepath=icon_path)
        elif icon_url:
            self.fetch_thread = IconFetchThread(icon_url, self)
            self.fetch_thread.finished.connect(self._on_icon_fetched)
            self.fetch_thread.start()
        else:
            # Fallback to first letter
            self.icon_label.setText(service_label[0] if service_label else "?")
            self.icon_label.setStyleSheet("background-color: #8b5cf6; color: white; border-radius: 8px; font-weight: bold; font-size: 16px;")
            
        layout.addWidget(self.icon_label)
        
        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        
        self.name_label = QtWidgets.QLabel(service_label)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 13px; color: palette(text);")
        
        self.status_label = QtWidgets.QLabel(self.tr("● (Activated)"))
        self.status_label.setStyleSheet("color: #4caf50; font-size: 11px; font-weight: bold; background-color: rgba(76, 175, 80, 0.1); border-radius: 4px; padding: 2px 4px;")
        self.status_label.hide()
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.status_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.update_style(False)
        
    def _set_icon_pixmap(self, data=None, filepath=None):
        try:
            is_svg = False
            if filepath and filepath.endswith('.svg'):
                is_svg = True
            elif data and (b'<svg' in data.lower() or b'<SVG' in data):
                is_svg = True

            dpr = self.devicePixelRatioF()
            target_size = int(32 * dpr)

            if is_svg:
                from PySide6.QtSvg import QSvgRenderer
                if data and (self.service_label == "9Router" or self.service_label == self.tr("9Router")):
                    # Fill the SVG with white for the orange background
                    data = data.replace(b'<svg', b'<svg fill="white"')

                if filepath:
                    renderer = QSvgRenderer(filepath)
                else:
                    renderer = QSvgRenderer(data)
                    
                pixmap = QtGui.QPixmap(target_size, target_size)
                pixmap.fill(QtCore.Qt.GlobalColor.transparent)
                pixmap.setDevicePixelRatio(dpr)
                
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
                # Ensure the SVG is rendered to the correct logical dimensions
                renderer.render(painter, QtCore.QRectF(0, 0, 32, 32))
                painter.end()
                
                self.icon_label.setPixmap(pixmap)
                return
        except Exception:
            pass

        # Fallback for non-SVG or if SVG rendering fails
        pixmap = QtGui.QPixmap()
        if filepath:
            pixmap.load(filepath)
        elif data:
            pixmap.loadFromData(data)
            
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(int(32 * self.devicePixelRatioF()), int(32 * self.devicePixelRatioF()), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            scaled_pixmap.setDevicePixelRatio(self.devicePixelRatioF())
            self.icon_label.setPixmap(scaled_pixmap)

    def _on_icon_fetched(self, data):
        self._set_icon_pixmap(data=data)
        
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.clicked.emit()
            
    def set_configured(self, is_configured):
        self.status_label.setVisible(is_configured)
        self.update_style(is_configured)
        
    def update_style(self, is_configured):
        if is_configured:
            self.setStyleSheet("""
                QFrame#ProviderCard {
                    border: 1px solid rgba(76, 175, 80, 0.5);
                    border-radius: 8px;
                    background-color: rgba(76, 175, 80, 0.05);
                }
                QFrame#ProviderCard:hover {
                    background-color: rgba(76, 175, 80, 0.1);
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#ProviderCard {
                    border: 1px solid rgba(128, 128, 128, 0.3);
                    border-radius: 8px;
                    background-color: transparent;
                }
                QFrame#ProviderCard:hover {
                    background-color: rgba(128, 128, 128, 0.1);
                }
            """)

class PlatformCredentialWidget(QtWidgets.QWidget):
    sig_credentials_changed = QtCore.Signal()
    sig_sign_in_clicked = QtCore.Signal()
    sig_sign_out_clicked = QtCore.Signal()
    sig_buy_credits_clicked = QtCore.Signal()

    def __init__(self, platform_display_name, platform_internal_name, parent=None):
        super().__init__(parent)
        self.platform_display_name = platform_display_name
        self.platform_internal_name = platform_internal_name
        self.widgets = {}
        self._init_ui()

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Header
        header = MLabel(self.platform_display_name).strong().h2()
        layout.addWidget(header)
        layout.addSpacing(10)

        # Fields based on platform
        if self.platform_internal_name == "Microsoft Azure":
            self._add_azure_fields(layout)
        elif self.platform_internal_name == "Custom":
            self._add_custom_fields(layout)
        elif self.platform_internal_name == "Yandex":
            self._add_yandex_fields(layout)
        elif self.platform_internal_name == "DeeLX":
            self._add_deelx_fields(layout)
        elif self.platform_internal_name == "Ollama":
            self._add_ollama_fields(layout)
        elif self.platform_internal_name == "9Router":
            self._add_9router_fields(layout)
        elif self.platform_internal_name == "Comic Translate (Official)":
            self._add_official_fields(layout)
        else:
            # Standard LLM platforms (Gemini, GPT, OpenRouter, Claude, Deepseek, DeepL, etc.)
            self._add_standard_llm_fields(layout)
            
        layout.addStretch(1)

    def _add_line_edit(self, layout, label_text, password=False):
        edit = MLineEdit()
        if password:
            edit.setEchoMode(QtWidgets.QLineEdit.Password)
        edit.setFixedWidth(400)
        prefix = MLabel(label_text).border()
        set_label_width(prefix)
        prefix.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        edit.set_prefix_widget(prefix)
        layout.addWidget(edit)
        # Notify when text changes (use lambda to ignore 'text' argument)
        edit.textChanged.connect(lambda: self.sig_credentials_changed.emit())
        return edit

    def _add_standard_llm_fields(self, layout):
        api_key_label = self.tr("API Key")
        if self.platform_internal_name == "DeepL":
            api_key_label = self.tr("Auth Key")
            
        self.api_key_input = self._add_line_edit(layout, api_key_label, password=True)
        self.widgets[f"{self.platform_internal_name}_api_key"] = self.api_key_input
        
        # If it's a platform that supports model fetching
        if self.platform_internal_name in ["Google Gemini", "Open AI GPT", "OpenRouter", "Anthropic Claude", "Deepseek"]:
            layout.addSpacing(15)
            
            fetch_layout = QtWidgets.QHBoxLayout()
            self.fetch_btn = MPushButton(self.tr("Fetch Models")).primary().small()
            self.fetch_btn.clicked.connect(self._fetch_models)
            fetch_layout.addWidget(self.fetch_btn)
            fetch_layout.addStretch(1)
            layout.addLayout(fetch_layout)
            
            layout.addSpacing(5)
            layout.addWidget(MLabel(self.tr("Model List")).secondary())
            
            # Model Search Bar
            self.model_search_input = MLineEdit().search().small()
            self.model_search_input.setPlaceholderText(self.tr("Search models..."))
            self.model_search_input.setFixedWidth(400)
            self.model_search_input.textChanged.connect(self._filter_models)
            layout.addWidget(self.model_search_input)
            
            self.model_list = QtWidgets.QListWidget()
            self.model_list.setFixedHeight(200)
            self.model_list.setFixedWidth(400)
            layout.addWidget(self.model_list)
            self.widgets[f"{self.platform_internal_name}_model_list"] = self.model_list

    def _filter_models(self, text: str):
        if not hasattr(self, 'model_list'):
            return
        for i in range(self.model_list.count()):
            item = self.model_list.item(i)
            # Case-insensitive search
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _add_azure_fields(self, layout):
        layout.addWidget(MLabel(self.tr("OCR")).secondary())
        self.widgets["Microsoft Azure_api_key_ocr"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Microsoft Azure_endpoint"] = self._add_line_edit(layout, self.tr("Endpoint URL"))
        
        layout.addSpacing(10)
        layout.addWidget(MLabel(self.tr("Translate")).secondary())
        self.widgets["Microsoft Azure_api_key_translator"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Microsoft Azure_region"] = self._add_line_edit(layout, self.tr("Region"))

    def _add_custom_fields(self, layout):
        self.widgets["Custom_api_key"] = self._add_line_edit(layout, self.tr("API Key"), password=True)
        self.widgets["Custom_api_url"] = self._add_line_edit(layout, self.tr("Endpoint URL"))
        self.widgets["Custom_model"] = self._add_line_edit(layout, self.tr("Model"))

    def _add_yandex_fields(self, layout):
        self.widgets["Yandex_api_key"] = self._add_line_edit(layout, self.tr("Secret Key"), password=True)
        self.widgets["Yandex_folder_id"] = self._add_line_edit(layout, self.tr("Folder ID"))

    def _add_ollama_fields(self, layout):
        self.url_input = self._add_line_edit(layout, self.tr("Base URL"))
        self.url_input.setPlaceholderText("http://localhost:11434")
        self.widgets["Ollama_api_url"] = self.url_input
        
        layout.addSpacing(15)
        
        fetch_layout = QtWidgets.QHBoxLayout()
        self.fetch_btn = MPushButton(self.tr("Fetch Models")).primary().small()
        self.fetch_btn.clicked.connect(self._fetch_models)
        fetch_layout.addWidget(self.fetch_btn)
        fetch_layout.addStretch(1)
        layout.addLayout(fetch_layout)
        
        layout.addSpacing(5)
        layout.addWidget(MLabel(self.tr("Model List")).secondary())
        
        # Model Search Bar
        self.model_search_input = MLineEdit().search().small()
        self.model_search_input.setPlaceholderText(self.tr("Search models..."))
        self.model_search_input.setFixedWidth(400)
        self.model_search_input.textChanged.connect(self._filter_models)
        layout.addWidget(self.model_search_input)
        
        self.model_list = QtWidgets.QListWidget()
        self.model_list.setFixedHeight(200)
        self.model_list.setFixedWidth(400)
        layout.addWidget(self.model_list)
        self.widgets["Ollama_model_list"] = self.model_list

    def _add_9router_fields(self, layout):
        self.url_input = self._add_line_edit(layout, self.tr("Base URL"))
        self.url_input.setText("http://localhost:20128/v1") # Default value
        self.widgets["9Router_api_url"] = self.url_input
        
        self.api_key_input = self._add_line_edit(layout, self.tr("API Key (Optional)"), password=True)
        self.widgets["9Router_api_key"] = self.api_key_input
        
        # If 9Router models can be fetched via standard OpenAI /v1/models,
        # we can add a fetch button later if needed.

    def _add_official_fields(self, layout):
        # Safety Warning
        warning_text = self.tr(
            "‼️ UnComicTranslate does not guarantee the safety of this platform. "
            "We forked from the original project a long time ago. The official "
            "login support is an independent option and is not associated with our project."
        )
        warning_label = MLabel(warning_text).secondary()
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #ff4d4f; font-size: 11px;") # Red color
        layout.addWidget(warning_label)
        layout.addSpacing(15)

        # 1. Account Section (Integrated)
        layout.addWidget(MLabel(self.tr("Official Account")).strong())
        
        # Logged Out State UI
        self.official_logged_out_widget = QtWidgets.QWidget()
        lo_layout = QtWidgets.QVBoxLayout(self.official_logged_out_widget)
        lo_layout.setContentsMargins(0, 0, 0, 0)
        self.sign_in_btn = MPushButton(self.tr("Sign In to Official Account")).primary().small()
        self.sign_in_btn.clicked.connect(self.sig_sign_in_clicked.emit)
        lo_layout.addWidget(self.sign_in_btn)
        layout.addWidget(self.official_logged_out_widget)
        
        # Logged In State UI
        self.official_logged_in_widget = QtWidgets.QWidget()
        li_layout = QtWidgets.QVBoxLayout(self.official_logged_in_widget)
        li_layout.setContentsMargins(0, 0, 0, 0)
        
        self.official_email_label = MLabel("...").secondary()
        self.official_credits_label = MLabel("...").secondary()
        li_layout.addWidget(self.official_email_label)
        li_layout.addWidget(self.official_credits_label)
        
        btn_layout = QtWidgets.QHBoxLayout()
        self.sign_out_btn = MPushButton(self.tr("Sign Out")).small()
        self.sign_out_btn.clicked.connect(self.sig_sign_out_clicked.emit)
        self.buy_credits_btn = MPushButton(self.tr("Buy Credits")).small()
        self.buy_credits_btn.clicked.connect(self.sig_buy_credits_clicked.emit)
        btn_layout.addWidget(self.buy_credits_btn)
        btn_layout.addWidget(self.sign_out_btn)
        btn_layout.addStretch(1)
        li_layout.addLayout(btn_layout)
        
        layout.addWidget(self.official_logged_in_widget)
        self.official_logged_in_widget.hide() # Default hidden

        layout.addSpacing(15)
        layout.addWidget(MLabel(self.tr("Translation Models")).strong())
        
        fetch_layout = QtWidgets.QHBoxLayout()
        self.fetch_btn = MPushButton(self.tr("Fetch Models")).primary().small()
        self.fetch_btn.clicked.connect(self._fetch_models)
        fetch_layout.addWidget(self.fetch_btn)
        fetch_layout.addStretch(1)
        layout.addLayout(fetch_layout)
        
        layout.addSpacing(5)
        layout.addWidget(MLabel(self.tr("Model List")).secondary())
        
        # Model Search Bar
        self.model_search_input = MLineEdit().search().small()
        self.model_search_input.setPlaceholderText(self.tr("Search models..."))
        self.model_search_input.setFixedWidth(400)
        self.model_search_input.textChanged.connect(self._filter_models)
        layout.addWidget(self.model_search_input)
        
        self.model_list = QtWidgets.QListWidget()
        self.model_list.setFixedHeight(150)
        self.model_list.setFixedWidth(400)
        layout.addWidget(self.model_list)
        self.widgets["Comic Translate (Official)_model_list"] = self.model_list

    def _add_deelx_fields(self, layout):
        self.enabled_checkbox = MCheckBox(self.tr("Enabled"))
        layout.addWidget(self.enabled_checkbox)
        self.widgets["DeeLX_self_hosted"] = self.enabled_checkbox
        
        self.url_input = self._add_line_edit(layout, self.tr("URL"))
        self.widgets["DeeLX_url"] = self.url_input
        
        self.url_input.setEnabled(self.enabled_checkbox.isChecked())
        self.enabled_checkbox.toggled.connect(self.url_input.setEnabled)
        self.enabled_checkbox.toggled.connect(lambda: self.sig_credentials_changed.emit())

    def _fetch_models(self):
        # For Official platform, we use global token exclusively
        if self.platform_internal_name == "Comic Translate (Official)":
            api_key = get_token("access_token")
        elif self.platform_internal_name == "Ollama":
            api_key = self.url_input.text() or "http://localhost:11434"
        else:
            api_key = self.api_key_input.text()

        if not api_key and self.platform_internal_name not in ["OpenRouter", "Ollama"]:
            MMessage.error(self.tr("Please enter an API Key first"), parent=self, duration=2)
            return

        # Show loading indicator (optional, but good UX)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText(self.tr("Fetching..."))
        
        # Use a thread for fetching to avoid UI freeze
        class FetchThread(QtCore.QThread):
            finished = QtCore.Signal(list)
            def __init__(self, platform, key):
                super().__init__()
                self.platform = platform
                self.key = key
            def run(self):
                models = []
                if self.platform == "Google Gemini":
                    models = ModelManager.fetch_gemini_models(self.key)
                elif self.platform == "OpenRouter":
                    models = ModelManager.fetch_openrouter_models(self.key)
                elif self.platform == "Open AI GPT":
                    models = ModelManager.fetch_openai_models(self.key)
                elif self.platform == "Anthropic Claude":
                    models = ModelManager.fetch_anthropic_models(self.key)
                elif self.platform == "Deepseek":
                    models = ModelManager.fetch_deepseek_models(self.key)
                elif self.platform == "Ollama":
                    models = ModelManager.fetch_ollama_models(self.key)
                elif self.platform == "Comic Translate (Official)":
                    models = ModelManager.fetch_official_models(self.key)
                self.finished.emit(models)

        self.thread = FetchThread(self.platform_internal_name, api_key)
        self.thread.finished.connect(self._on_models_fetched)
        self.thread.start()

    def _on_models_fetched(self, models):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText(self.tr("Fetch Models"))
        
        if not models:
            MMessage.warning(self.tr("No models found or error occurred"), parent=self, duration=2)
            return

        self.model_list.clear()
        self.model_list.addItems(models)
        MMessage.success(self.tr(f"Fetched {len(models)} models"), parent=self, duration=2)


class CredentialsPage(QtWidgets.QWidget):
    sig_sign_in_clicked = QtCore.Signal()
    sig_sign_out_clicked = QtCore.Signal()
    sig_buy_credits_clicked = QtCore.Signal()

    def __init__(self, services: list[str], value_mappings: dict[str, str], parent=None):
        super().__init__(parent)
        self.services = services
        self.value_mappings = value_mappings
        self.credential_widgets = {} # Flat dictionary for backward compatibility
        self.platform_widgets = {}

        # main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Global Header (Search + Save Keys)
        self.global_header = QtWidgets.QWidget()
        header_layout = QtWidgets.QVBoxLayout(self.global_header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Save Keys Checkbox
        self.save_keys_checkbox = MCheckBox(self.tr("Save Keys"))
        header_layout.addWidget(self.save_keys_checkbox)
        header_layout.addSpacing(5)

        # Provider Search Bar
        self.provider_search_bar = MLineEdit().search().small()
        self.provider_search_bar.setPlaceholderText(self.tr("Search providers..."))
        self.provider_search_bar.textChanged.connect(self._filter_providers)
        header_layout.addWidget(self.provider_search_bar)
        
        main_layout.addWidget(self.global_header)
        main_layout.addSpacing(10)

        # Stacked Widget
        self.stacked_widget = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Grid Page (Page 0)
        self.grid_page = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.grid_page)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        self.stacked_widget.addWidget(self.grid_page)

        self.provider_buttons = []
        row = 0
        col = 0
        max_cols = 3

        page_index = 1
        for i, service_label in enumerate(self.services):
            internal_name = self.value_mappings.get(service_label, service_label)
            
            # Create Card/Button for Grid
            btn = ProviderCard(service_label=service_label)

            
            if internal_name == "Googletrans":
                btn.clicked.connect(self._show_googletrans_warning)
            else:
                # Capture the index for the closure
                btn.clicked.connect(lambda checked=False, idx=page_index: self.stacked_widget.setCurrentIndex(idx))
                page_index += 1
            
            self.provider_buttons.append((service_label, btn))
            self.grid_layout.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
            
            if internal_name != "Googletrans":
                platform_widget = PlatformCredentialWidget(service_label, internal_name)
                platform_widget.sig_credentials_changed.connect(self.update_status_indicators)
                platform_widget.sig_sign_in_clicked.connect(self.sig_sign_in_clicked.emit)
                platform_widget.sig_sign_out_clicked.connect(self.sig_sign_out_clicked.emit)
                platform_widget.sig_buy_credits_clicked.connect(self.sig_buy_credits_clicked.emit)
                
                # Add Back Button
                back_btn = MPushButton(text=self.tr("← Back to Providers")).small()
                back_btn.setFixedWidth(150)
                back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
                platform_widget.layout().insertWidget(0, back_btn)
                platform_widget.layout().insertSpacing(1, 10)
                
                self.stacked_widget.addWidget(platform_widget)
                self.platform_widgets[internal_name] = platform_widget
                
                # Merge widgets into the flat dictionary for SettingsPage to access
                self.credential_widgets.update(platform_widget.widgets)

        # Add vertical stretch to push the grid to the top
        self.grid_layout.setRowStretch(row + 1, 1)
        # Add horizontal stretch to the last column to push things left
        self.grid_layout.setColumnStretch(max_cols, 1)

        # Connect page change signal after initialization to avoid early calls
        self.stacked_widget.currentChanged.connect(self._on_page_changed)
        # Initial update of indicators
        self.update_status_indicators()

    def _on_page_changed(self, index: int):
        # Only show the global header (Search/Save) on the grid page (index 0)
        self.global_header.setVisible(index == 0)

        # Initial update of indicators
        self.update_status_indicators()

    def _filter_providers(self, text: str):
        # Clear current grid items (without deleting widgets)
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.takeAt(i)
            # We don't need to do anything with 'item' as the widgets are still owned by grid_page
            
        row = 0
        col = 0
        max_cols = 3
        
        for label, btn in self.provider_buttons:
            if text.lower() in label.lower():
                btn.show()
                self.grid_layout.addWidget(btn, row, col)
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            else:
                btn.hide()
        
        # Re-apply stretch
        self.grid_layout.setRowStretch(row + 1, 1)
        for r in range(row + 1):
            self.grid_layout.setRowStretch(r, 0)

    def update_status_indicators(self):
        for label, btn in self.provider_buttons:
            internal_name = self.value_mappings.get(label, label)
            widget = self.platform_widgets.get(internal_name)
            
            is_configured = False
            
            if internal_name == "Googletrans":
                is_configured = True
            elif not widget: 
                continue
            # Check primary API key or custom fields
            elif internal_name == "Microsoft Azure":
                ocr_key = widget.widgets.get("Microsoft Azure_api_key_ocr")
                tr_key = widget.widgets.get("Microsoft Azure_api_key_translator")
                if (ocr_key and ocr_key.text().strip()) or (tr_key and tr_key.text().strip()):
                    is_configured = True
            elif internal_name == "DeeLX":
                url = widget.widgets.get("DeeLX_url")
                if url and url.text().strip():
                    is_configured = True
            elif internal_name == "Custom":
                url = widget.widgets.get("Custom_api_url")
                if url and url.text().strip():
                    is_configured = True
            elif internal_name == "Ollama":
                url = widget.widgets.get("Ollama_api_url")
                model_list = widget.widgets.get("Ollama_model_list")
                # Ollama is considered configured if either URL is set or a model is selected
                if (url and url.text().strip()) or (model_list and model_list.currentItem()):
                    is_configured = True
            elif internal_name == "9Router":
                url = widget.widgets.get("9Router_api_url")
                if url and url.text().strip():
                    is_configured = True
            elif internal_name == "Comic Translate (Official)":
                if get_token("access_token"):
                    is_configured = True
            else:
                key_input = widget.widgets.get(f"{internal_name}_api_key")
                if key_input and hasattr(key_input, 'text') and key_input.text().strip():
                    is_configured = True
            
            if hasattr(btn, 'set_configured'):
                btn.set_configured(is_configured)
            else:
                prefix = "🟢 " if is_configured else ""
                clean_label = label.replace("🟢 ", "")
                btn.setText(f"{prefix}{clean_label}")

    def _show_googletrans_warning(self):
        MMessage.warning(
            self.tr("⭕ This is an unofficial version. It might be blocked by Google or the quality might not be good."),
            parent=self,
            duration=5
        )

