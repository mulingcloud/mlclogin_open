import os
import re
import random
from pathlib import Path
from datetime import datetime
from typing import Union, Optional

from mlcbase import (Logger, ConfigDict, SQLiteAPI, encrypt_password, verify_password, 
                     verify_otp_code)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import (QCloseEvent, QIcon, QKeySequence, QShortcut, QColor, QDesktopServices, 
                           QPixmap)
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, 
                               QSizePolicy, QLabel, QStackedWidget, QFrame, QFileDialog)
from qfluentwidgets import (CheckBox, HyperlinkLabel, LineEdit, PasswordLineEdit, 
                            PrimaryPushButton, PushButton, BodyLabel, TabBar, 
                            InfoBar, InfoBarPosition, MessageBoxBase, SubtitleLabel,
                            CaptionLabel, PixmapLabel)

from .common import resource_rc
from ..backend import ConfigFile, Database, EmailServer, SFTPAPI, get_table_field_index, load_image_from_path


class LoginForm:
    def __init__(self, Login: QWidget):
        self.formLayout = QVBoxLayout()
        self.formLayout.setObjectName("formLayout")
        self.formFrame = QFrame(Login)
        self.formFrame.setObjectName("formFrame")
        self.formFrame.setStyleSheet("""
            background: rgb(242,242,242);
            border-radius: 8px;
        """)
        self.formFrame.setFrameStyle(QFrame.Shape.Box)
        self.formFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.formFrame.setLineWidth(0)
        self.formFrame.setLayout(self.formLayout)

        hspacer = QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.loginUsernameLabel = BodyLabel(Login)
        self.loginUsernameLabel.setObjectName("loginUsernameLabel")
        self.loginUsernameLabel.setText(Login.tr("Username or Email:"))
        self.formLayout.addWidget(self.loginUsernameLabel)
        self.loginUsernameLineEdit = LineEdit(Login)
        self.loginUsernameLineEdit.setClearButtonEnabled(True)
        self.loginUsernameLineEdit.setObjectName("loginUsernameLineEdit")
        self.formLayout.addWidget(self.loginUsernameLineEdit)
        self.loginPasswordLabel = BodyLabel(Login)
        self.loginPasswordLabel.setObjectName("loginPasswordLabel")
        self.loginPasswordLabel.setText(Login.tr("Password:"))
        self.formLayout.addWidget(self.loginPasswordLabel)
        self.loginPasswordLineEdit = PasswordLineEdit(Login)
        self.loginPasswordLineEdit.setObjectName("loginPasswordLineEdit")
        self.formLayout.addWidget(self.loginPasswordLineEdit)
        self.loginAttachLayout = QHBoxLayout()
        self.loginAttachLayout.setObjectName("loginAttachLayout")
        self.savePasswordCheckBox = CheckBox(Login)
        self.savePasswordCheckBox.setObjectName("savePasswordCheckBox")
        self.savePasswordCheckBox.setChecked(Login.cfg.frontend.login.save_password)
        self.savePasswordCheckBox.setText(Login.tr("Save Password"))
        self.loginAttachLayout.addWidget(self.savePasswordCheckBox)
        self.loginAttachLayout.addItem(hspacer)
        self.retrievePasswordLabel = HyperlinkLabel(Login)
        self.retrievePasswordLabel.setObjectName("retrievePasswordLabel")
        self.retrievePasswordLabel.setText(Login.tr("Retrieve Password"))
        self.loginAttachLayout.addWidget(self.retrievePasswordLabel)
        self.formLayout.addLayout(self.loginAttachLayout)


class SignupForm:
    def __init__(self, Login: QWidget):
        self.formLayout = QVBoxLayout()
        self.formLayout.setObjectName("formLayout")
        self.formFrame = QFrame(Login)
        self.formFrame.setObjectName("formFrame")
        self.formFrame.setStyleSheet("""
            background: rgb(242,242,242);
            border-radius: 8px;
        """)
        self.formFrame.setFrameStyle(QFrame.Shape.Box)
        self.formFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.formFrame.setLineWidth(0)
        self.formFrame.setLayout(self.formLayout)

        self.signupUsernameLabel = BodyLabel(Login)
        self.signupUsernameLabel.setObjectName("signupUsernameLabel")
        self.signupUsernameLabel.setText(Login.tr("Username:"))
        self.formLayout.addWidget(self.signupUsernameLabel)
        self.signupUsernameLineEdit = LineEdit(Login)
        self.signupUsernameLineEdit.setClearButtonEnabled(True)
        self.signupUsernameLineEdit.setObjectName("signupUsernameLineEdit")
        self.formLayout.addWidget(self.signupUsernameLineEdit)
        self.signupPasswordLabel = BodyLabel(Login)
        self.signupPasswordLabel.setObjectName("signupPasswordLabel")
        self.signupPasswordLabel.setText(Login.tr("Password:"))
        self.formLayout.addWidget(self.signupPasswordLabel)
        self.signupPasswordLineEdit = PasswordLineEdit(Login)
        self.signupPasswordLineEdit.setObjectName("signupPasswordLineEdit")
        self.formLayout.addWidget(self.signupPasswordLineEdit)
        self.signupConfirmPasswordLabel = BodyLabel(Login)
        self.signupConfirmPasswordLabel.setObjectName("signupConfirmPasswordLabel")
        self.signupConfirmPasswordLabel.setText(Login.tr("Confirm Password:"))
        self.formLayout.addWidget(self.signupConfirmPasswordLabel)
        self.signupConfirmPasswordLineEdit = PasswordLineEdit(Login)
        self.signupConfirmPasswordLineEdit.setObjectName("signupConfirmPasswordLineEdit")
        self.formLayout.addWidget(self.signupConfirmPasswordLineEdit)
        self.signupEmailLabel = BodyLabel(Login)
        self.signupEmailLabel.setObjectName("signupEmailLabel")
        self.signupEmailLabel.setText(Login.tr("Email:"))
        self.formLayout.addWidget(self.signupEmailLabel)
        self.signupEmailLineEdit = LineEdit(Login)
        self.signupEmailLineEdit.setClearButtonEnabled(True)
        self.signupEmailLineEdit.setObjectName("signupEmailLineEdit")
        self.formLayout.addWidget(self.signupEmailLineEdit)
        self.emailVerifyLayout = QHBoxLayout()
        self.emailVerifyLayout.setObjectName("emailVerifyLayout")
        self.emailVerifyLineEdit = LineEdit(Login)
        self.emailVerifyLineEdit.setClearButtonEnabled(True)
        self.emailVerifyLineEdit.setObjectName("emailVerifyLineEdit")
        self.emailVerifyLayout.addWidget(self.emailVerifyLineEdit)
        self.emailSendCodeButton = PushButton(Login)
        self.emailSendCodeButton.setObjectName("emailSendCodeButton")
        self.emailSendCodeButton.setText(Login.tr("Send Code"))
        self.emailSendCodeButton.setFixedWidth(100)
        self.emailVerifyLayout.addWidget(self.emailSendCodeButton)
        self.formLayout.addLayout(self.emailVerifyLayout)
        self.uploadAvatarLayout = QVBoxLayout()
        self.uploadButtonsLayout = QHBoxLayout()
        self.uploadAvatarHyperlinkLabel = HyperlinkLabel(Login)
        self.uploadAvatarHyperlinkLabel.setObjectName("uploadAvatarHyperlinkLabel")
        self.uploadAvatarHyperlinkLabel.setText(Login.tr("Upload Avatar"))
        self.uploadAvatarHyperlinkLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.uploadButtonsLayout.addWidget(self.uploadAvatarHyperlinkLabel)
        self.uploadButtonsLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.cancelAvatarHyperlinkLabel = HyperlinkLabel(Login)
        self.cancelAvatarHyperlinkLabel.setObjectName("cancelAvatarHyperlinkLabel")
        self.cancelAvatarHyperlinkLabel.setText("✖️")
        self.cancelAvatarHyperlinkLabel.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        self.cancelAvatarHyperlinkLabel.hide()
        self.uploadButtonsLayout.addWidget(self.cancelAvatarHyperlinkLabel)
        self.uploadButtonsLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.uploadAvatarLayout.addLayout(self.uploadButtonsLayout)
        self.avatarLabel = PixmapLabel(Login)
        self.avatarLabel.setObjectName("avatarLabel")
        self.avatarLabel.setFixedSize(Login.cfg.frontend.signup.avatar_width, Login.cfg.frontend.signup.avatar_height)
        self.avatarLabel.hide()
        self.uploadAvatarLayout.addWidget(self.avatarLabel)
        self.formLayout.addLayout(self.uploadAvatarLayout)
        self.formLayout.addItem(QSpacerItem(10, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        self.signupAttachLayout = QHBoxLayout()
        self.signupAttachLayout.setObjectName("signupAttachLayout")
        self.signupAgreeTermsCheckBox = CheckBox(Login)
        self.signupAgreeTermsCheckBox.setObjectName("signupAgreeTermsCheckBox")
        self.signupAgreeTermsCheckBox.setText(Login.tr("I agree to the \"User Agreement\""))
        self.signupAttachLayout.addWidget(self.signupAgreeTermsCheckBox)
        self.signupAttachLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.signupUserAgreementLabel = HyperlinkLabel(Login)
        self.signupUserAgreementLabel.setObjectName("signupUserAgreementLabel")
        self.signupUserAgreementLabel.setText(Login.tr("User Agreement"))
        self.signupAttachLayout.addWidget(self.signupUserAgreementLabel)
        self.formLayout.addLayout(self.signupAttachLayout)


class LoginUI:
    def setupUi(self, Login: QWidget):
        self.run_counter = 0
        self.currentForm = "login"
        self.Form = Login

        self.windowLayout = QVBoxLayout(Login)
        self.windowLayout.setObjectName("windowLayout")

        self.tabBar = TabBar(Login)
        self.tabBar.setTabsClosable(False)
        self.tabBar.setAddButtonVisible(False)
        self.tabBar.setTabMaximumWidth(Login.cfg.frontend.login.window_width // 4)
        self.stackedWidget = QStackedWidget(Login)
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.loginTabLabel = BodyLabel(Login)
        self.signupTabLabel = BodyLabel(Login)
        self.addSubInterface(self.loginTabLabel, "loginTabLabel", Login.tr("Login"))
        self.addSubInterface(self.signupTabLabel, "signupTabLabel", Login.tr("Sign up"))
        self.windowLayout.addWidget(self.tabBar)
        self.loginForm = LoginForm(Login)
        self.signupForm = SignupForm(Login)
        self.signupForm.formFrame.setHidden(True)
        self.signupForm.formFrame.setDisabled(True)
        self.windowLayout.addWidget(self.loginForm.formFrame)

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName("buttonLayout")
        self.confirmButton = PrimaryPushButton(Login)
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setText(Login.tr("Confirm"))
        self.buttonLayout.addWidget(self.confirmButton)
        self.clearButton = PushButton(Login)
        self.clearButton.setObjectName("clearButton")
        self.clearButton.setText(Login.tr("Clear"))
        self.buttonLayout.addWidget(self.clearButton)
        self.windowLayout.addLayout(self.buttonLayout)

    def onCurrentIndexChanged(self, index):
        widget = self.stackedWidget.widget(index)
        if not widget:
            return
        
        if widget.objectName() == "loginTabLabel":
            if self.run_counter == 0:
                self.run_counter += 1
            else:
                self.signupForm.formFrame.setHidden(True)
                self.signupForm.formFrame.setDisabled(True)
                self.loginForm.formFrame.setHidden(False)
                self.loginForm.formFrame.setDisabled(False)
                self.windowLayout.replaceWidget(self.signupForm.formFrame, self.loginForm.formFrame)
                self.Form.set_fixed_window(self.Form.cfg.frontend.login.window_width, self.Form.cfg.frontend.login.window_height)
                self.Form.set_centered_window()
                self.currentForm = "login"

        if widget.objectName() == "signupTabLabel":
            self.loginForm.formFrame.setHidden(True)
            self.loginForm.formFrame.setDisabled(True)
            self.signupForm.formFrame.setHidden(False)
            self.signupForm.formFrame.setDisabled(False)
            self.windowLayout.replaceWidget(self.loginForm.formFrame, self.signupForm.formFrame)
            if self.Form.signup_upload_avatar_flag:
                self.Form.set_fixed_window(self.Form.cfg.frontend.signup.window_width, 
                                           self.Form.cfg.frontend.signup.window_height + self.Form.cfg.frontend.signup.avatar_height)
            else:
                self.Form.set_fixed_window(self.Form.cfg.frontend.signup.window_width, self.Form.cfg.frontend.signup.window_height)
            self.Form.set_centered_window()
            self.currentForm = "signup"

    def addSubInterface(self, widget: QLabel, objectName, text):
        widget.setObjectName(objectName)
        widget.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.stackedWidget.addWidget(widget)
        self.tabBar.addTab(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )


class Verify2FA(MessageBoxBase):
    def __init__(self, parent, secret):
        super().__init__(parent)
        self.secret = secret
        self.matched = False

        self.titleLabel = SubtitleLabel(self.tr("2FA Verification"), self)

        self.verifyCodeLineEdit = LineEdit(self)
        self.verifyCodeLineEdit.setClearButtonEnabled(True)

        self.warningLabel = CaptionLabel(self.tr("The verification code is incorrect"))
        self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.verifyCodeLineEdit)
        self.viewLayout.addWidget(self.warningLabel)
        self.warningLabel.hide()

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(300)

    def validate(self):
        code = self.verifyCodeLineEdit.text()
        matched = verify_otp_code(code=code, 
                                  secret_key=self.secret, 
                                  method="TOTP",
                                  valid_window=1,
                                  logger=self.parent().logger)
        if not matched:
            self.warningLabel.show()
            return False
        
        self.matched = matched
        return True


class RetrievePassword(MessageBoxBase):
    def __init__(self, parent):
        super().__init__(parent)
        self.titleLabl = SubtitleLabel(self.tr("Retrieve Password"), self)

        self.emailLineEdit = LineEdit(self)
        self.emailLineEdit.setPlaceholderText(self.tr("Email Address"))
        self.emailLineEdit.setClearButtonEnabled(True)

        self.codeLayout = QHBoxLayout()
        self.codeLineEdit = LineEdit(self)
        self.codeLineEdit.setPlaceholderText(self.tr("Verification Code"))
        self.codeLineEdit.setClearButtonEnabled(True)
        self.codeLayout.addWidget(self.codeLineEdit)
        self.sendCodeButton = PushButton(self.tr("Send Code"), self)
        self.sendCodeButton.setFixedWidth(100)
        self.codeLayout.addWidget(self.sendCodeButton)

        self.warningLabel = CaptionLabel()
        self.warningLabel.hide()

        self.viewLayout.addWidget(self.titleLabl)
        self.viewLayout.addWidget(self.emailLineEdit)
        self.viewLayout.addLayout(self.codeLayout)
        self.viewLayout.addWidget(self.warningLabel)

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(350)

        self.send_email_interval = self.parent().cfg.backend.signup.send_email_interval
        self.yes_button_click_interval = self.parent().cfg.backend.button_click_interval
        self.send_verify_code = False
        self.send_verify_code_time = None
        self.verify_code = None
        self.verify_success = False
        self.email = None

        self.sendCodeTimer = QTimer(self)
        self.yesButtonTimer = QTimer(self)
        self.sendCodeButton.clicked.connect(self.send_code)
        self.sendCodeTimer.timeout.connect(self.update_send_code_timer)
        self.yesButtonTimer.timeout.connect(self.update_yes_button_timer)

    def validate(self):
        if self.yesButtonTimer.isActive():
            self.warningLabel.setText(self.tr("You click too quickly."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False
        self.yesButtonTimer.start(1000)

        if not self.send_verify_code:
            self.warningLabel.setText(self.tr("Please send verification code first."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False
        
        now_time = datetime.now()
        elapsed = (now_time-self.send_verify_code_time).total_seconds()
        if elapsed > self.parent().cfg.backend.signup.email_verify_code_timeout:
            self.warningLabel.setText(self.tr("Verification code has beed expired."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False
        
        code = self.codeLineEdit.text()
        if code != self.verify_code:
            self.warningLabel.setText(self.tr("Verification code is incorrect."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False

        self.verify_success = True
        return True
    
    def send_code(self):
        email = self.emailLineEdit.text()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.warningLabel.setText(self.tr("Invalid email address."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return
        else:
            self.warningLabel.hide()
        
        self.sendCodeButton.setDisabled(True)
        exist_user = self.parent().db.api.search_data(table_name=self.parent().cfg.backend.user_table_name,
                                                      condition=f"email='{email}'")
        if len(exist_user) == 0:
            self.warningLabel.setText(self.tr("This email address is not registered."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            self.sendCodeButton.setDisabled(False)
            return
        
        verify_code = random.choices("0123456789", k=self.parent().cfg.backend.signup.email_verify_code_digits)
        self.verify_code = "".join(verify_code)
        if self.parent().cfg.frontend.language == "zh_CN":
            email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                您正在重置密码，请确认是您本人的操作，不要将验证泄漏给他人！
                            </div>
                            <div align="center" style="font-family: Microsoft YaHei; font-size: 18px; font-weight: bold; color: white; margin-top: 15px; margin-bottom: 15px">
                                <span style="background-color: rgb(152, 48, 68); padding: 10px; border-radius: 8px">验证码：{self.verify_code}</span>
                            </div>
                            <div style="font-family: Microsoft YaHei; font-size: 16px;">
                                本验证码<span style="font-weight: bold;">{self.parent()._second2minute(self.parent().cfg.backend.signup.email_verify_code_timeout)}分钟</span>内有效。
                            </div>"""
        elif self.parent().cfg.frontend.language == "en_US":
            email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                You are resetting your password. Please confirm that it was your own operation and do not leak the verification to others!
                            </div>
                            <div align="center" style="font-family: Microsoft YaHei; font-size: 18px; font-weight: bold; color: white; margin-top: 15px; margin-bottom: 15px">
                                <span style="background-color: rgb(152, 48, 68); padding: 10px; border-radius: 8px">{self.tr("Verification Code: ")}{self.verify_code}</span>
                            </div>
                            <div style="font-family: Microsoft YaHei; font-size: 16px;">
                                This verification code will be expired after: <span style="font-weight: bold;">{self.parent()._second2minute(self.parent().cfg.backend.signup.email_verify_code_timeout)} minutes</span>
                            </div>"""
        send_status = self.parent().email_server.api.send_email(
            receiver_name=exist_user[0][get_table_field_index(self.parent().cfg, "backend", self.parent().cfg.backend.user_table_name, "username")],
            receiver_email=email,
            subject=self.tr("MuLingCloud | Reset Password Verification Code"),
            content=email_content,
            signature=self.parent().email_server.SIGNATURE
        )

        if send_status:
            self.email = self.emailLineEdit.text()
            self.send_verify_code_time = datetime.now()
            self.send_verify_code = True
            self.sendCodeButton.setText(str(self.send_email_interval))
            self.sendCodeTimer.start(1000)
            self.warningLabel.setText(self.tr("Verification code sent."))
            self.warningLabel.setTextColor(QColor(0, 128, 0), QColor(51, 204, 51))
            self.warningLabel.show()
        else:
            self.warningLabel.setText(self.tr("Failed to send verification code."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
    
    def update_send_code_timer(self):
        self.send_email_interval -= 1
        self.sendCodeButton.setText(str(self.send_email_interval))
        if self.send_email_interval == 0:
            self.send_email_interval = self.parent().cfg.backend.signup.send_email_interval
            self.sendCodeButton.setDisabled(False)
            self.sendCodeButton.setText(self.tr("Send Code"))
            self.sendCodeTimer.stop()

    def update_yes_button_timer(self):
        self.yes_button_click_interval -= 1
        if self.yes_button_click_interval == 0:
            self.yes_button_click_interval = self.parent().cfg.backend.button_click_interval
            self.yesButtonTimer.stop()
            

class ResetPassword(MessageBoxBase):
    def __init__(self, parent, email):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr("Reset Password"), self)
        self.viewLayout.addWidget(self.titleLabel)
        
        self.passwordLineEdit = PasswordLineEdit()
        self.passwordLineEdit.setPlaceholderText(self.tr("New password"))
        self.confirmPasswordLineEdit = PasswordLineEdit()
        self.confirmPasswordLineEdit.setPlaceholderText(self.tr("Confirm password"))
        self.viewLayout.addWidget(self.passwordLineEdit)
        self.viewLayout.addWidget(self.confirmPasswordLineEdit)

        self.warningLabel = CaptionLabel()
        self.warningLabel.hide()
        self.viewLayout.addWidget(self.warningLabel)

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(300)

        self.reset_success = False
        self.reset_email = email

    def validate(self):
        def has_letter(s):
            return bool(re.search(r'[a-zA-Z]', s))

        def has_digit(s):
            return bool(re.search(r'[0-9]', s))
        
        password = self.passwordLineEdit.text()
        confirm_password = self.confirmPasswordLineEdit.text()
        
        if len(password) < 8:
            self.warningLabel.setText(self.tr("Password must be at least 8 characters."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False
        
        if not (has_letter(password) and has_digit(password)):
            self.warningLabel.setText(self.tr("Password must contain letters and digits."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False
        
        if password != confirm_password:
            self.warningLabel.setText(self.tr("Passwords do not match."))
            self.warningLabel.setTextColor(QColor(207, 16, 16), QColor(255, 28, 32))
            self.warningLabel.show()
            return False

        status = self.parent().db.api.update_data(table_name=self.parent().cfg.backend.user_table_name,
                                                  data=dict(password=encrypt_password(password, self.parent().cfg.backend.password_hash_method)),
                                                  condition=f"email='{self.reset_email}'")
        if status:
            self.reset_success = True
            return True
        else:
            return False


class Login(QWidget, LoginUI):
    ROOT = Path(__file__).parent.parent.parent.parent
    UI_ROOT = Path(__file__).parent
    loginSuccessSignal = Signal(ConfigDict, ConfigFile)
    
    def __init__(self, config: Union[str, Path, ConfigFile], logger: Optional[Logger] = None):
        super().__init__()
        if logger is None:
            self.logger = Logger()
            self.logger.init_logger()
        else:
            self.logger = logger
        if isinstance(config, (str, Path)):
            self.cfg = ConfigFile(config)
        else:
            self.cfg = config
        self._check_config()

        # load local secret
        temp_db_path = self.UI_ROOT / "common" / "temp.sqlite"
        if temp_db_path.exists():
            self.temp_secret = SQLiteAPI(temp_db_path, logger=self.logger)
            saved_user = self.temp_secret.search_data(table_name="saved_userpasswd", list_all=True)
            if len(saved_user) > 0:
                self.loginForm.loginUsernameLineEdit.setText(saved_user[0][1])
                self.loginForm.loginPasswordLineEdit.setText(saved_user[0][2])
                self.loginForm.savePasswordCheckBox.setChecked(True)
        else:
            self.temp_secret = None

        # init window
        self.init_window()

        # parameters
        self.db = Database(self.cfg, self.logger)
        self.email_server = EmailServer(self.cfg, self.logger)
        self.sftp = SFTPAPI(self.cfg, self.logger)
        self.ping_seconds = self.cfg.backend.ping_seconds
        self.login_confirm_button_click_interval = self.cfg.backend.button_click_interval
        self.signup_confirm_button_click_interval = self.cfg.backend.button_click_interval
        self.signup_send_email_code = False
        self.signup_send_email_code_time = None
        self.signup_email_verify_code = None
        self.signup_send_email_inverval = self.cfg.backend.signup.send_email_interval
        self.signup_upload_avatar_flag = False
        self.signup_upload_avatar_path = None
        self.signup_read_user_agreement = False
        self.is_jump = False

        # signals
        self.init_signal()

        # shortcut
        self.return_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)  # 回车
        self.enter_shorcut = QShortcut(QKeySequence(Qt.Key.Key_Enter), self)  # 小键盘
        self.return_shortcut.activated.connect(self.confirm)
        self.enter_shorcut.activated.connect(self.confirm)

    def init_window(self):
        self.setObjectName("Login")
        self.setWindowTitle(self.tr("Login"))
        if self.cfg.frontend.fixed_window:
            self.setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowCloseButtonHint)
        self.set_fixed_window(self.cfg.frontend.login.window_width, self.cfg.frontend.login.window_height)
        self.set_centered_window()
        self.setWindowIcon(QIcon(":/login/image/logo.png"))
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setStyleSheet("Login{background: white}")
        self.setupUi(self)

    def set_fixed_window(self, width: int, height: int):
        if self.cfg.frontend.login.fixed_window:
            self.resize(width, height)
            self.setFixedSize(width, height)

    def set_centered_window(self):
        if self.cfg.frontend.centered_window:
            desktop = QApplication.screens()[0].availableGeometry()
            w, h = desktop.width(), desktop.height()
            self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def init_signal(self):
        self.pingTimer = QTimer(self)
        self.pingTimer.start(1000)
        self.loginConfirmButtonTimer = QTimer(self)
        self.signupSendCodeTimer = QTimer(self)
        self.signupConfirmButtonTimer = QTimer(self)

        self.pingTimer.timeout.connect(self.ping)
        self.loginConfirmButtonTimer.timeout.connect(self.update_login_confirm_button_timer)
        self.signupSendCodeTimer.timeout.connect(self.update_email_timer)
        self.signupConfirmButtonTimer.timeout.connect(self.update_signup_confirm_button_timer)
        self.confirmButton.clicked.connect(self.confirm)
        self.clearButton.clicked.connect(self.clear)
        self.loginForm.retrievePasswordLabel.clicked.connect(self.retrieve_password)
        self.signupForm.emailSendCodeButton.clicked.connect(self._send_email_verify_code)
        self.signupForm.uploadAvatarHyperlinkLabel.clicked.connect(self.upload_avatar)
        self.signupForm.cancelAvatarHyperlinkLabel.clicked.connect(self.cancel_avatar)
        self.signupForm.signupUserAgreementLabel.clicked.connect(self.read_user_agreement)

    def confirm(self):
        if self.currentForm == "login":
            if self.loginConfirmButtonTimer.isActive():
                self.warn_status(self.tr("You clicked too quickly."))
                return
            self.loginConfirmButtonTimer.start(1000)

            now_time = datetime.now()
            username = self.loginForm.loginUsernameLineEdit.text()
            password = self.loginForm.loginPasswordLineEdit.text()
            is_save_password = self.loginForm.savePasswordCheckBox.isChecked()

            db_user_info = self.db.api.search_data(table_name=self.cfg.backend.user_table_name, condition=f"username='{username}' OR email='{username}'")
            if len(db_user_info) == 0:
                self.error_status(self.tr("User does not exist."))
                return
            db_user_info = db_user_info[0]
            
            account_enable = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "enable")]
            if account_enable == 0:
                self.error_status(self.tr("This account is disabled."))
                return
            
            # reach max failed times
            login_failed_times = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "login_failed_times")]
            if login_failed_times == self.cfg.backend.login.max_failed_times:
                last_login_failed_time = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "last_login_failed_time")]
                elapsed = (now_time - last_login_failed_time).total_seconds()
                if elapsed < self.cfg.backend.login.lock_time:
                    last_lock_time = int(self.cfg.backend.login.lock_time - elapsed)
                    last_lock_time = str(int(self._second2minute(last_lock_time))+1)
                    if self.cfg.frontend.language == "zh_CN":
                        error_msg = f"该账户已被锁定，请{last_lock_time}分钟后再尝试"
                    if self.cfg.frontend.language == "en_US":
                        error_msg = f"This account has been locked, please try after {last_lock_time} minutes."
                    self.error_status(error_msg)
                    return
                else:
                    login_failed_times = 0
                    self.db.api.update_data(table_name=self.cfg.backend.user_table_name,
                                            data=dict(login_failed_times=login_failed_times),
                                            condition=f"username='{username}' OR email='{username}'")

            # password not match
            if not verify_password(
                password, 
                db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "password")], 
                self.cfg.backend.password_hash_method
            ):
                login_failed_times += 1
                last_attempts = self.cfg.backend.login.max_failed_times - login_failed_times
                if last_attempts > 0:
                    if self.cfg.frontend.language == "zh_CN":
                        error_msg = f"密码错误，您还可以尝试{last_attempts}次"
                    if self.cfg.frontend.language == "en_US":
                        error_msg = f"Password is incorrect. You can also try {last_attempts} times."
                else:
                    if self.cfg.frontend.language == "zh_CN":
                        error_msg = "密码错误，该账户已被锁定"
                    if self.cfg.frontend.language == "en_US":
                        error_msg = "Password is incorrect. This account has been locked."
                
                self.error_status(error_msg)
                self.db.api.update_data(table_name=self.cfg.backend.user_table_name,
                                        data=dict(login_failed_times=login_failed_times, 
                                                  last_login_failed_time=now_time.strftime("%Y-%m-%d %H:%M:%S")),
                                        condition=f"username='{username}' OR email='{username}'")
                return
            
            # 2FA
            if self.cfg.backend.login.enable_2FA:
                secret_2fa = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "2FA")]
                if secret_2fa is not None:
                    self.return_shortcut.setEnabled(False)
                    self.enter_shorcut.setEnabled(False)
                    window_2FA = Verify2FA(self, secret_2fa)
                    window_2FA.exec()
                    self.return_shortcut.setEnabled(True)
                    self.enter_shorcut.setEnabled(True)
                    if not window_2FA.matched:
                        return 
            
            # login success
            username = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "username")]
            if is_save_password:
                if self.temp_secret is None:
                    self.temp_secret = SQLiteAPI(self.UI_ROOT/"common"/"temp.sqlite", logger=self.logger)
                    self.temp_secret.create_table(
                        table_name="saved_userpasswd",
                        table_config=[dict(name="id", dtype="integer", not_null=True, primary_key=True, auto_increment=True),
                                      dict(name="username", dtype="text", not_null=True),
                                      dict(name="password", dtype="text", not_null=True)]
                    )

                saved_user = self.temp_secret.search_data(table_name="saved_userpasswd", list_all=True)
                if len(saved_user) == 0:
                    self.temp_secret.insert_data(table_name="saved_userpasswd", data=dict(username=username, password=password))
            else:
                if self.temp_secret is not None:
                    saved_user = self.temp_secret.search_data(table_name="saved_userpasswd", list_all=True)
                    if len(saved_user) > 0:
                        self.temp_secret.delete_data(table_name="saved_userpasswd", condition=f"username='{saved_user[0][1]}'")
            access_times = db_user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "access_times")]
            self.db.api.update_data(table_name=self.cfg.backend.user_table_name,
                                    data=dict(access_times=access_times+1, 
                                              last_login_time=now_time.strftime("%Y-%m-%d %H:%M:%S"),
                                              login_failed_times=0),
                                    condition=f"username='{username}'")
            self.success_status(self.tr("Login success"))
            self.login_success_jump(db_user_info)

        elif self.currentForm == "signup":
            if self.signupConfirmButtonTimer.isActive():
                self.warn_status(self.tr("You clicked too quickly."))
                return
            self.signupConfirmButtonTimer.start(1000)

            if not self.signup_read_user_agreement:
                self.warn_status(self.tr("Please read the User Agreement first."))
                return
            if not self.signupForm.signupAgreeTermsCheckBox.isChecked():
                self.warn_status(self.tr("Please agree to the User Agreement."))
                return
            
            username = self.signupForm.signupUsernameLineEdit.text()
            password = self.signupForm.signupPasswordLineEdit.text()
            confirm_password = self.signupForm.signupConfirmPasswordLineEdit.text()
            email = self.signupForm.signupEmailLineEdit.text()
            email_verify_code = self.signupForm.emailVerifyLineEdit.text()

            if not self._signup_verify_username(username):
                return 
            if not self._signup_verify_password(password, confirm_password):
                return
            if not self._signup_verify_email(email, email_verify_code):
                return
            
            # upload avatar
            if self.signup_upload_avatar_flag:
                suffix = Path(self.signup_upload_avatar_path).suffix
                remote_path = f"{self.sftp.remote_root}/user/avatar/{username}{suffix}"
                if not self.sftp.api.upload_file(
                    local_path=self.signup_upload_avatar_path, 
                    remote_path=remote_path, 
                    remote_platform=self.sftp.remote_platform
                ):
                    self.error_status(self.tr("Upload avatar failed."))
                    return
            
            # set mulingcloud account
            cipher = encrypt_password(password, self.cfg.backend.password_hash_method)
            data = dict(username=username, 
                        password=cipher, 
                        enable=1, 
                        authority="User",
                        email=email,
                        signup_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        access_times=0,
                        login_failed_times=0,
                        avatar=1 if self.signup_upload_avatar_flag else 0)
            signup_status = self.db.api.insert_data(table_name=self.cfg.backend.user_table_name, data=data)
            if signup_status:
                if self.cfg.frontend.language == "zh_CN":
                    email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                        恭喜您，注册成功！请牢记您的用户名：<span style="font-weight: bold;">{username}</span>
                                        </div>"""
                elif self.cfg.frontend.language == "en_US":
                    email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                        Congratulations! Signup successfully. Please remember your MuLingCloud username: <span style="font-weight: bold;">{username}</span>
                                        </div>"""
                self.email_server.api.send_email(receiver_name=username,
                                                 receiver_email=email,
                                                 subject=self.tr("MuLingCloud | Signup Success"),
                                                 content=email_content,
                                                 signature=self.email_server.SIGNATURE)
                self.success_status(self.tr("Congratulations! Signup successfully."))
                self.signup_send_email_code = False
                self.signup_send_email_code_time = None
                self.signup_email_verify_code = None
                self.signup_read_user_agreement = False
                if self.signupSendCodeTimer.isActive():
                    self.signup_send_email_inverval = self.cfg.backend.signup.send_email_interval
                    self.signupForm.emailSendCodeButton.setDisabled(False)
                    self.signupForm.emailSendCodeButton.setText(self.tr("Send Code"))
                    self.signupSendCodeTimer.stop()
                self.clear()
                self.tabBar.setCurrentIndex(0)
                self.stackedWidget.setCurrentIndex(0)
            else:
                self.error_status(self.tr("Signup failed. Please try again later."))

    def retrieve_password(self):
        self.return_shortcut.setEnabled(False)
        self.enter_shorcut.setEnabled(False)
        window_retrieve_password = RetrievePassword(self)
        window_retrieve_password.exec()
        if window_retrieve_password.verify_success:
            window_reset_password = ResetPassword(self, window_retrieve_password.email)
            window_reset_password.exec()
            if window_reset_password.reset_success:
                reset_username = self.db.api.search_data(table_name=self.cfg.backend.user_table_name,
                                                         fields="username",
                                                         condition=f"email='{window_retrieve_password.email}'")[0][0]
                self.loginForm.loginUsernameLineEdit.clear()
                self.loginForm.loginPasswordLineEdit.clear()
                self.loginForm.savePasswordCheckBox.setChecked(False)
                if self.temp_secret is not None:
                    saved_user = self.temp_secret.search_data(table_name="saved_userpasswd", list_all=True)
                    if len(saved_user) > 0:
                        saved_username = saved_user[0][1]
                        if reset_username == saved_username:
                            self.temp_secret.delete_data(table_name="saved_userpasswd", condition=f"username='{saved_username}'")
                if self.cfg.frontend.language == "zh_CN":
                    email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                        重置密码成功！请使用新密码登录。
                                        </div>"""
                elif self.cfg.frontend.language == "en_US":
                    email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                        Password reset successfully! Please login with your new password.
                                        </div>"""
                self.email_server.api.send_email(receiver_name=reset_username,
                                                 receiver_email=window_retrieve_password.email,
                                                 subject=self.tr("MuLingCloud | Reset Password Success"),
                                                 content=email_content,
                                                 signature=self.email_server.SIGNATURE)
                self.success_status(self.tr("Password reset successfully!"))
        self.return_shortcut.setEnabled(True)
        self.enter_shorcut.setEnabled(True)

    def upload_avatar(self):
        # load avatar to cache
        allow_suffix = [f"*{suffix}" for suffix in self.cfg.backend.signup.avatar_suffix]
        allow_suffix = " ".join(allow_suffix)
        filepath, _ = QFileDialog.getOpenFileName(self, 
                                                  caption=self.tr("Select Avatar"), 
                                                  dir=os.path.expanduser("~"),
                                                  filter=f"{self.tr("Image file")} ({allow_suffix})")
        if filepath == "":
            return
        
        suffix = Path(filepath).suffix
        cache_path = self.ROOT / "cache" / f"avatar{suffix}"
        if suffix == ".png":
            color_model = "RGBA"
        else:
            color_model = "RGB"
        avatar = load_image_from_path(filepath, self.cfg.backend.signup.avatar_size, color_mode=color_model)
        avatar.save(str(cache_path))

        # show avatar preview
        preview = QPixmap(str(cache_path)).scaled(self.cfg.frontend.signup.avatar_width, 
                                                  self.cfg.frontend.signup.avatar_height,
                                                  Qt.AspectRatioMode.KeepAspectRatio,
                                                  Qt.TransformationMode.SmoothTransformation)
        self.signupForm.avatarLabel.setPixmap(preview)
        self.signupForm.avatarLabel.show()
        self.signupForm.cancelAvatarHyperlinkLabel.show()
        self.set_fixed_window(self.cfg.frontend.signup.window_width, 
                              self.cfg.frontend.signup.window_height+self.cfg.frontend.signup.avatar_height)
        self.set_centered_window()

        # set parameter
        self.signup_upload_avatar_flag = True
        self.signup_upload_avatar_path = str(cache_path)

    def cancel_avatar(self):
        os.remove(self.signup_upload_avatar_path)
        self.signup_upload_avatar_flag = False
        self.signup_upload_avatar_path = None
        self.signupForm.avatarLabel.hide()
        self.signupForm.cancelAvatarHyperlinkLabel.hide()
        self.set_fixed_window(self.cfg.frontend.signup.window_width, self.cfg.frontend.signup.window_height)
        self.set_centered_window()
            
    def read_user_agreement(self):
        QDesktopServices.openUrl(QUrl(self.cfg.backend.user_agreement_url))
        self.signup_read_user_agreement = True
            
    def clear(self):
        if self.currentForm == "login":
            self.loginForm.loginUsernameLineEdit.clear()
            self.loginForm.loginPasswordLineEdit.clear()
            self.loginForm.savePasswordCheckBox.setChecked(False)
        elif self.currentForm == "signup":
            self.signupForm.signupUsernameLineEdit.clear()
            self.signupForm.signupPasswordLineEdit.clear()
            self.signupForm.signupConfirmPasswordLineEdit.clear()
            self.signupForm.signupEmailLineEdit.clear()
            self.signupForm.emailVerifyLineEdit.clear()
            self.signupForm.signupAgreeTermsCheckBox.setChecked(False)
            if self.signup_upload_avatar_flag:
                self.cancel_avatar()

    def _send_email_verify_code(self):
        if not self.signup_read_user_agreement:
            self.warn_status(self.tr("Please read the User Agreement first"))
            return
        
        username = self.signupForm.signupUsernameLineEdit.text()
        if not self._signup_verify_username(username):
            return 
        email = self.signupForm.signupEmailLineEdit.text()
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.error_status(self.tr("Invalid email address."))
            return
        
        self.signupForm.emailSendCodeButton.setDisabled(True)
        verify_code = random.choices("0123456789", k=self.cfg.backend.signup.email_verify_code_digits)
        self.signup_email_verify_code = "".join(verify_code)
        if self.cfg.frontend.language == "zh_CN":
            email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                亲爱的<span style="font-weight: bold;">{username}</span>，欢迎注册牧灵云MuLingCloud用户！
                            </div>
                            <div align="center" style="font-family: Microsoft YaHei; font-size: 18px; font-weight: bold; color: white; margin-top: 15px; margin-bottom: 15px">
                                <span style="background-color: rgb(152, 48, 68); padding: 10px; border-radius: 8px">验证码：{self.signup_email_verify_code}</span>
                            </div>
                            <div style="font-family: Microsoft YaHei; font-size: 16px;">
                                本验证码<span style="font-weight: bold;">{self._second2minute(self.cfg.backend.signup.email_verify_code_timeout)}分钟</span>内有效。
                            </div>"""
        elif self.cfg.frontend.language == "en_US":
            email_content = f"""<div style="font-family: Microsoft YaHei; font-size: 16px;">
                                    Dear <span style="font-weight: bold;">{username}</span>, welcome to register as a user of MuLingCloud!
                                </div>
                                <div align="center" style="font-family: Microsoft YaHei; font-size: 18px; font-weight: bold; color: white; margin-top: 15px; margin-bottom: 15px">
                                    <span style="background-color: rgb(152, 48, 68); padding: 10px; border-radius: 8px">Verification Code: {self.signup_email_verify_code}</span>
                                </div>
                                <div style="font-family: Microsoft YaHei; font-size: 16px;">
                                    This verification code will be expired after: <span style="font-weight: bold;">{self._second2minute(self.cfg.backend.signup.email_verify_code_timeout)} minutes</span>
                                </div>"""
        send_status = self.email_server.api.send_email(receiver_name=username,
                                                       receiver_email=email,
                                                       subject=self.tr("MuLingCloud | Signup Verification Code"),
                                                       content=email_content,
                                                       signature=self.email_server.SIGNATURE)
        if send_status:
            self.signup_send_email_code_time = datetime.now()
            self.signup_send_email_code = True
            self.signupForm.emailSendCodeButton.setText(str(self.signup_send_email_inverval))
            self.signupSendCodeTimer.start(1000)  # trigger timeout signal every 1 second
            self.success_status(self.tr("Verification code sent."))
        else:
            self.signupForm.emailSendCodeButton.setDisabled(False)
            self.error_status(self.tr("Failed to send verification code. Please try again later."))

    def update_login_confirm_button_timer(self):
        self.login_confirm_button_click_interval -= 1
        if self.login_confirm_button_click_interval == 0:
            self.login_confirm_button_click_interval = self.cfg.backend.button_click_interval
            self.loginConfirmButtonTimer.stop()

    def update_email_timer(self):
        self.signup_send_email_inverval -= 1
        self.signupForm.emailSendCodeButton.setText(str(self.signup_send_email_inverval))
        if self.signup_send_email_inverval == 0:
            self.signup_send_email_inverval = self.cfg.backend.signup.send_email_interval
            self.signupForm.emailSendCodeButton.setDisabled(False)
            self.signupForm.emailSendCodeButton.setText(self.tr("Send Code"))
            self.signupSendCodeTimer.stop()

    def update_signup_confirm_button_timer(self):
        self.signup_confirm_button_click_interval -= 1
        if self.signup_confirm_button_click_interval == 0:
            self.signup_confirm_button_click_interval = self.cfg.backend.button_click_interval
            self.signupConfirmButtonTimer.stop()

    def _signup_verify_username(self, username: str):
        if len(username) < 3:
            self.error_status(self.tr("Username must be at least 3 characters long."))
            return False

        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(pattern, username):
            self.error_status(self.tr("Username can only contain letters, numbers, - and _."))
            return False
        
        exist_username = self.db.api.search_data(self.cfg.backend.user_table_name, condition=f"username=\'{username}\'")
        if len(exist_username) > 0:
            self.error_status(self.tr("Username already exists."))
            return False
        
        return True

    def _signup_verify_password(self, password: str, confirm_password: str):
        def has_letter(s):
            return bool(re.search(r'[a-zA-Z]', s))

        def has_digit(s):
            return bool(re.search(r'[0-9]', s))
        
        if len(password) < 8:
            self.error_status(self.tr("Password must be at least 8 characters."))
            return False
        
        if not (has_letter(password) and has_digit(password)):
            self.error_status(self.tr("Password must contain letters and digits."))
            return False
        
        if password != confirm_password:
            self.error_status(self.tr("Passwords do not match."))
            return False
        
        return True
    
    def _signup_verify_email(self, email: str, code: str):
        if email == "":
            self.error_status(self.tr("Email cannot be empty."))
            return False
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.error_status(self.tr("Invalid email address."))
            return False
        
        if not self.signup_send_email_code:
            self.error_status(self.tr("Please send a verification code to your email."))
            return False
        
        now_time = datetime.now()
        elapsed = (now_time-self.signup_send_email_code_time).total_seconds()
        if elapsed > self.cfg.backend.signup.email_verify_code_timeout:
            self.error_status(self.tr("Verification code has beed expired."))
            return False
        
        if code != self.signup_email_verify_code:
            self.error_status(self.tr("Verification code is incorrect."))
            return False
        
        return True
    
    def success_status(self, content):
        InfoBar.success(title=self.tr("Success"),
                        content=content,
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self)

    def error_status(self, content):
        InfoBar.error(title=self.tr("Error"),
                      content=content,
                      orient=Qt.Orientation.Horizontal,
                      position=InfoBarPosition.TOP,
                      duration=2000,
                      parent=self)
        
    def warn_status(self, content):
        InfoBar.warning(title=self.tr("Warning"),
                        content=content,
                        orient=Qt.Orientation.Horizontal,
                        position=InfoBarPosition.TOP,
                        duration=2000,
                        parent=self)
        
    def _second2minute(self, second: Union[int, float], return_decimal: bool = False):
        minute = str(second//60)
        decimal = second%60
        if decimal > 0 and return_decimal:
            minute =  minute + "." + str(decimal)
        return minute
    
    def _check_config(self):
        if self.cfg.backend.signup.email_verify_code_timeout < 60:
            self.logger.error("email_verify_code_timeout cannot not less than 60 seconds")
            raise ValueError("email_verify_code_timeout cannot not less than 60 seconds")
        if self.cfg.backend.ping_seconds < 10:
            self.logger.error("ping_seconds cannot less than 10 seconds")
            raise ValueError("ping_seconds cannot less than 10 seconds")
        if self.cfg.backend.database.backend == "sqlite" and self.cfg.backend.database.connect.need_ping:
            self.logger.error("sqlite database does not support ping")
            raise ValueError("sqlite database does not support ping")
        if self.cfg.backend.login.max_failed_times < 1:
            self.logger.error("max_failed_times cannot less than 1")
            raise ValueError("max_failed_times cannot less than 1")
    
    def ping(self):
        self.ping_seconds -= 1
        if self.ping_seconds <= 0:
            if self.cfg.backend.database.connect.need_ping:
                self.db.ping()
            if self.cfg.backend.email.connect.need_ping:
                self.email_server.ping()
            if self.cfg.backend.sftp.connect.need_ping:
                self.sftp.ping()
            self.ping_seconds = self.cfg.backend.ping_seconds

    def close_api(self):
        self.db.close()
        self.email_server.close()
        if self.temp_secret is not None:
            self.temp_secret.close()
    
    def stop_timer(self):
        if self.pingTimer.isActive():
            self.pingTimer.stop()
        if self.loginConfirmButtonTimer.isActive():
            self.loginConfirmButtonTimer.stop()
        if self.signupSendCodeTimer.isActive():
            self.signupSendCodeTimer.stop()

    def closeEvent(self, event: QCloseEvent):
        if not self.is_jump:
            self.close_api()
        self.stop_timer()
        super().closeEvent(event)

    def login_success_jump(self, user_info):
        self.is_jump = True
        self.close()
        self.db.secret.save_secret("user_info", "username", user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "username")])
        self.db.secret.save_secret("user_info", "email", user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "email")])
        if user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "2FA")] is not None:
            self.db.secret.save_secret("user_info", "2FA", user_info[get_table_field_index(self.cfg, "backend", self.cfg.backend.user_table_name, "2FA")])
        apis = ConfigDict(db=self.db, email_server=self.email_server, sftp=self.sftp, temp_secret=self.temp_secret)
        self.loginSuccessSignal.emit(apis, self.cfg)
