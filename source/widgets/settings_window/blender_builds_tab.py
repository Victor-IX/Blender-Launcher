from modules.settings import (
    blender_minimum_versions,
    favorite_pages,
    get_bash_arguments,
    get_blender_startup_arguments,
    get_check_for_new_builds_automatically,
    get_check_for_new_builds_on_startup,
    get_enable_quick_launch_key_seq,
    get_install_template,
    get_launch_blender_no_console,
    get_mark_as_favorite,
    get_minimum_blender_stable_version,
    get_new_builds_check_frequency,
    get_platform,
    get_quick_launch_key_seq,
    get_scrape_automated_builds,
    get_scrape_stable_builds,
    get_scrape_alternative_stable_builds,
    get_show_daily_archive_builds,
    get_show_experimental_archive_builds,
    get_show_patch_archive_builds,
    set_bash_arguments,
    set_blender_startup_arguments,
    set_check_for_new_builds_automatically,
    set_check_for_new_builds_on_startup,
    set_enable_quick_launch_key_seq,
    set_install_template,
    set_launch_blender_no_console,
    set_mark_as_favorite,
    set_minimum_blender_stable_version,
    set_new_builds_check_frequency,
    set_quick_launch_key_seq,
    set_scrape_automated_builds,
    set_scrape_stable_builds,
    set_scrape_alternative_stable_builds,
    set_show_daily_archive_builds,
    set_show_experimental_archive_builds,
    set_show_patch_archive_builds,
)
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
)
from widgets.settings_form_widget import SettingsFormWidget

from .settings_group import SettingsGroup


class BlenderBuildsTabWidget(SettingsFormWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Checking for builds settings
        self.buildcheck_settings = SettingsGroup("Checking For Builds", parent=self)

        # Minimum stable blender download version (this is mainly for cleanliness and speed)
        self.MinStableBlenderVer = QComboBox()
        self.MinStableBlenderVer.addItems(blender_minimum_versions.keys())
        self.MinStableBlenderVer.setCurrentIndex(get_minimum_blender_stable_version())
        self.MinStableBlenderVer.activated[str].connect(self.change_minimum_blender_stable_version)

        # Whether to check for new builds based on a timer
        self.CheckForNewBuildsAutomatically = QCheckBox()
        self.CheckForNewBuildsAutomatically.setChecked(False)
        self.CheckForNewBuildsAutomatically.clicked.connect(self.toggle_check_for_new_builds_automatically)
        self.CheckForNewBuildsAutomatically.setText("Check automatically")
        # How often to check for new builds if ^^ enabled
        self.NewBuildsCheckFrequency = QSpinBox()
        self.NewBuildsCheckFrequency.setEnabled(get_check_for_new_builds_automatically())
        self.NewBuildsCheckFrequency.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.NewBuildsCheckFrequency.setToolTip("Time in hours between new builds check")
        self.NewBuildsCheckFrequency.setMaximum(24 * 7 * 4)  # 4 weeks?
        self.NewBuildsCheckFrequency.setMinimum(12)
        self.NewBuildsCheckFrequency.setPrefix("Interval: ")
        self.NewBuildsCheckFrequency.setSuffix("h")
        self.NewBuildsCheckFrequency.setValue(get_new_builds_check_frequency())
        self.NewBuildsCheckFrequency.editingFinished.connect(self.new_builds_check_frequency_changed)
        # Whether to check on startup
        self.CheckForNewBuildsOnStartup = QCheckBox()
        self.CheckForNewBuildsOnStartup.setChecked(get_check_for_new_builds_on_startup())
        self.CheckForNewBuildsOnStartup.clicked.connect(self.toggle_check_on_startup)
        self.CheckForNewBuildsOnStartup.setText("On startup")

        # Scraping builds settings
        self.ScrapeStableBuilds = QCheckBox(self)
        self.ScrapeStableBuilds.setChecked(get_scrape_stable_builds())
        self.ScrapeStableBuilds.clicked.connect(self.toggle_scrape_stable_builds)
        self.ScrapeStableBuilds.setText("Scrape Stable Builds")
        self.ScrapeAlternativeStableBuilds = QCheckBox(self)
        self.ScrapeAlternativeStableBuilds.setChecked(get_scrape_alternative_stable_builds())
        self.ScrapeAlternativeStableBuilds.clicked.connect(self.toggle_scrape_alternative_stable_builds)
        self.ScrapeAlternativeStableBuilds.setText("Scrape Alternative Stable Builds")
        self.ScrapeAutomatedBuilds = QCheckBox(self)
        self.ScrapeAutomatedBuilds.setChecked(get_scrape_automated_builds())
        self.ScrapeAutomatedBuilds.clicked.connect(self.toggle_scrape_automated_builds)
        self.ScrapeAutomatedBuilds.setText("Scrape Automated Builds (daily/experimental/patch)")

        # Show Archive Builds
        self.show_daily_archive_builds = QCheckBox(self)
        self.show_daily_archive_builds.setText("Show Daily Archive Builds")
        self.show_daily_archive_builds.setChecked(get_show_daily_archive_builds())
        self.show_daily_archive_builds.clicked.connect(self.toggle_show_daily_archive_builds)
        self.show_experimental_archive_builds = QCheckBox(self)
        self.show_experimental_archive_builds.setText("Show Experimental Archive Builds")
        self.show_experimental_archive_builds.setChecked(get_show_experimental_archive_builds())
        self.show_experimental_archive_builds.clicked.connect(self.toggle_show_experimental_archive_builds)
        self.show_patch_archive_builds = QCheckBox(self)
        self.show_patch_archive_builds.setText("Show Patch Archive Builds")
        self.show_patch_archive_builds.setChecked(get_show_patch_archive_builds())
        self.show_patch_archive_builds.clicked.connect(self.toggle_show_patch_archive_builds)

        # Layout
        self.scraping_builds_layout = QGridLayout()
        self.scraping_builds_layout.addWidget(self.CheckForNewBuildsAutomatically, 0, 0, 1, 1)
        self.scraping_builds_layout.addWidget(self.NewBuildsCheckFrequency, 0, 1, 1, 1)
        self.scraping_builds_layout.addWidget(self.CheckForNewBuildsOnStartup, 1, 0, 1, 2)
        self.scraping_builds_layout.addWidget(QLabel("Minimum stable build to scrape", self), 2, 0, 1, 1)
        self.scraping_builds_layout.addWidget(self.MinStableBlenderVer, 2, 1, 1, 1)
        self.scraping_builds_layout.addWidget(self.ScrapeStableBuilds, 3, 0, 1, 2)
        self.scraping_builds_layout.addWidget(self.ScrapeAlternativeStableBuilds, 4, 0, 1, 2)
        self.scraping_builds_layout.addWidget(self.ScrapeAutomatedBuilds, 5, 0, 1, 2)
        self.scraping_builds_layout.addWidget(self.show_daily_archive_builds, 6, 0, 1, 2)
        self.scraping_builds_layout.addWidget(self.show_experimental_archive_builds, 7, 0, 1, 2)
        self.scraping_builds_layout.addWidget(self.show_patch_archive_builds, 8, 0, 1, 2)
        self.buildcheck_settings.setLayout(self.scraping_builds_layout)

        # Downloading builds settings
        self.download_settings = SettingsGroup("Downloading & Saving Builds", parent=self)

        # Mark As Favorite
        self.EnableMarkAsFavorite = QCheckBox()
        self.EnableMarkAsFavorite.setText("Mark as Favorite")
        self.EnableMarkAsFavorite.setChecked(get_mark_as_favorite() != 0)
        self.EnableMarkAsFavorite.clicked.connect(self.toggle_mark_as_favorite)
        self.MarkAsFavorite = QComboBox()
        self.MarkAsFavorite.addItems([fav for fav in favorite_pages if fav != "Disable"])
        self.MarkAsFavorite.setCurrentIndex(max(get_mark_as_favorite() - 1, 0))
        self.MarkAsFavorite.activated[str].connect(self.change_mark_as_favorite)
        self.MarkAsFavorite.setEnabled(self.EnableMarkAsFavorite.isChecked())

        # Install Template
        self.InstallTemplate = QCheckBox()
        self.InstallTemplate.setText("Install Template")
        self.InstallTemplate.clicked.connect(self.toggle_install_template)
        self.InstallTemplate.setChecked(get_install_template())

        self.downloading_layout = QGridLayout()
        self.downloading_layout.addWidget(self.EnableMarkAsFavorite, 0, 0, 1, 1)
        self.downloading_layout.addWidget(self.MarkAsFavorite, 0, 1, 1, 1)
        self.downloading_layout.addWidget(self.InstallTemplate, 1, 0, 1, 2)
        self.download_settings.setLayout(self.downloading_layout)

        # Launching builds settings
        self.launching_settings = SettingsGroup("Launching Builds", parent=self)

        # Quick Launch Key Sequence
        self.EnableQuickLaunchKeySeq = QCheckBox()
        self.EnableQuickLaunchKeySeq.setText("Quick Launch Global Shortcut")
        self.EnableQuickLaunchKeySeq.clicked.connect(self.toggle_enable_quick_launch_key_seq)
        self.EnableQuickLaunchKeySeq.setChecked(get_enable_quick_launch_key_seq())
        self.QuickLaunchKeySeq = QLineEdit()
        self.QuickLaunchKeySeq.setEnabled(get_enable_quick_launch_key_seq())
        self.QuickLaunchKeySeq.keyPressEvent = self._keyPressEvent
        self.QuickLaunchKeySeq.setText(str(get_quick_launch_key_seq()))
        self.QuickLaunchKeySeq.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.QuickLaunchKeySeq.setCursorPosition(0)
        self.QuickLaunchKeySeq.editingFinished.connect(self.update_quick_launch_key_seq)
        # Run Blender using blender-launcher.exe
        self.LaunchBlenderNoConsole = QCheckBox()
        self.LaunchBlenderNoConsole.setText("Hide Console On Startup")
        self.LaunchBlenderNoConsole.clicked.connect(self.toggle_launch_blender_no_console)
        self.LaunchBlenderNoConsole.setChecked(get_launch_blender_no_console())
        # Blender Startup Arguments
        self.BlenderStartupArguments = QLineEdit()
        self.BlenderStartupArguments.setText(str(get_blender_startup_arguments()))
        self.BlenderStartupArguments.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.BlenderStartupArguments.setCursorPosition(0)
        self.BlenderStartupArguments.editingFinished.connect(self.update_blender_startup_arguments)
        # Command Line Arguments
        self.BashArguments = QLineEdit()
        self.BashArguments.setText(str(get_bash_arguments()))
        self.BashArguments.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.BashArguments.setCursorPosition(0)
        self.BashArguments.editingFinished.connect(self.update_bash_arguments)

        self.launching_layout = QFormLayout()
        self.launching_layout.addRow(self.EnableQuickLaunchKeySeq, self.QuickLaunchKeySeq)
        if get_platform() == "Windows":
            self.launching_layout.addRow(self.LaunchBlenderNoConsole)
        self.launching_layout.addRow(QLabel("Startup Arguments:", self))
        self.launching_layout.addRow(self.BlenderStartupArguments)
        if get_platform() == "Linux":
            self.launching_layout.addRow(QLabel("Bash Arguments:", self))
            self.launching_layout.addRow(self.BashArguments)
        self.launching_settings.setLayout(self.launching_layout)

        # Layout
        self.addRow(self.buildcheck_settings)
        self.addRow(self.download_settings)
        self.addRow(self.launching_settings)

    def change_mark_as_favorite(self, page):
        set_mark_as_favorite(page)

    def change_minimum_blender_stable_version(self, proxy_type):
        set_minimum_blender_stable_version(proxy_type)

    def update_blender_startup_arguments(self):
        args = self.BlenderStartupArguments.text()
        set_blender_startup_arguments(args)

    def update_bash_arguments(self):
        args = self.BashArguments.text()
        set_bash_arguments(args)

    def toggle_install_template(self, is_checked):
        set_install_template(is_checked)

    def toggle_mark_as_favorite(self, is_checked):
        self.MarkAsFavorite.setEnabled(is_checked)
        if is_checked:
            set_mark_as_favorite(self.MarkAsFavorite.currentText())
        else:
            set_mark_as_favorite("Disable")

    def toggle_launch_blender_no_console(self, is_checked):
        set_launch_blender_no_console(is_checked)

    def update_quick_launch_key_seq(self):
        key_seq = self.QuickLaunchKeySeq.text()
        set_quick_launch_key_seq(key_seq)

    def toggle_enable_quick_launch_key_seq(self, is_checked):
        set_enable_quick_launch_key_seq(is_checked)
        self.QuickLaunchKeySeq.setEnabled(is_checked)

    def _keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        MOD_MASK = Qt.Modifier.CTRL | Qt.Modifier.ALT | Qt.Modifier.SHIFT
        key_name = ""
        key = e.key()
        modifiers = int(e.modifiers())

        if (
            modifiers
            and modifiers & MOD_MASK == modifiers
            and key > 0
            and key not in {Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Control, Qt.Key.Key_Meta}
        ):
            key_name = QtGui.QKeySequence(modifiers + key).toString()
        elif not modifiers and (key != Qt.Key.Key_Meta):
            key_name = QtGui.QKeySequence(key).toString()

        if key_name != "":
            # Remap <Shift + *> keys sequences
            if "Shift" in key_name:
                alt_chars = '~!@#$%^&*()_+|{}:"<>?'
                real_chars = r"`1234567890-=\[];',./"
                trans_table = str.maketrans(alt_chars, real_chars)
                trans = key_name[-1].translate(trans_table)
                key_name = key_name[:-1] + trans

            self.QuickLaunchKeySeq.setText(key_name.lower())

        return super().keyPressEvent(e)

    def toggle_check_for_new_builds_automatically(self, is_checked):
        set_check_for_new_builds_automatically(is_checked)
        self.NewBuildsCheckFrequency.setEnabled(is_checked)

    def new_builds_check_frequency_changed(self):
        set_new_builds_check_frequency(self.NewBuildsCheckFrequency.value() * 60)

    def toggle_check_on_startup(self, is_checked):
        set_check_for_new_builds_on_startup(is_checked)
        self.CheckForNewBuildsOnStartup.setChecked(is_checked)

    def toggle_scrape_stable_builds(self, is_checked):
        set_scrape_stable_builds(is_checked)
        self.ScrapeStableBuilds.setChecked(is_checked)
    
    def toggle_scrape_alternative_stable_builds(self, is_checked):
        set_scrape_alternative_stable_builds(is_checked)
        self.ScrapeAlternativeStableBuilds.setChecked(is_checked)

    def toggle_scrape_automated_builds(self, is_checked):
        set_scrape_automated_builds(is_checked)
        self.ScrapeAutomatedBuilds.setChecked(is_checked)

    def toggle_show_daily_archive_builds(self, is_checked):
        set_show_daily_archive_builds(is_checked)
        self.show_daily_archive_builds.setChecked(is_checked)

    def toggle_show_experimental_archive_builds(self, is_checked):
        set_show_experimental_archive_builds(is_checked)
        self.show_experimental_archive_builds.setChecked(is_checked)

    def toggle_show_patch_archive_builds(self, is_checked):
        set_show_patch_archive_builds(is_checked)
        self.show_patch_archive_builds.setChecked(is_checked)
