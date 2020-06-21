#######################################################
SUDO=""
INSTALL_PYTHON38="no"
PYTHON="python3.8"
DO_UNINSTALL_PIPS="no"
USER="mark"
#######################################################

if [ "$INSTALL_PYTHON38" = "yes" ] ; then
  echo "[$0] Installing python 3.8"
  # Enable package from amazon linux
  $SUDO amazon-linux-extras enable python3.8

  $SUDO yum clean metadata
  $SUDO yum install python38
else
  echo "[$0] Not installing python 3.8"
fi

$SUDO $PYTHON -m pip install --upgrade pip

#
# xmlsec lib will fail on python3.8
# Thus these will be left out
#   xmlsec==1.3.3
#
pip_packages="
  gunicorn==20.0.4
  Flask==1.1.2
    itsdangerous==1.1.0
    click==7.1.2
    Jinja2==2.11.2
    MarkupSafe==1.1.1
    Werkzeug==1.0.1
  requests==2.24.0
    idna==2.9
    chardet==3.0.4
    certifi==2020.4.5.2
    urllib3==1.25.9
  numpy==1.18.5
  pandas==1.0.5
    six==1.15.0
  scipy==1.4.1
  hanziconv==0.3.2
  nltk==3.5
    joblib==0.15.1
    regex==2020.6.8
    tqdm==4.46.1
  googletrans==3.0.0
  pycryptodome==3.9.7
  pyotp==2.3.0
  gevent==20.6.2
    greenlet==0.4.16
  gevent-websocket==0.10.1
  websockets==8.1
  Flask-Cors==3.0.8
  Pillow==7.1.2
  opencv-python==4.2.0.34
  opencv-python-headless==4.2.0.34
  furl==2.1.0
  iso-639==0.4.5
    lxml==4.5.1
  defusedxml==0.6.0
  isodate==0.6.0
  configparser==5.0.0
"
#
# Uninstall packages
#
if [ "$DO_UNINSTALL_PIPS" = "yes" ] ; then
  for pkg in $pip_packages ; do
      # Remove version
      pkg=$(echo "$pkg" | sed s/"==.*"/""/g)
      echo "pip install $pkg..."
      $SUDO $PYTHON -m pip uninstall "$pkg"
  done
fi

# Reinstall packages
for pkg in $pip_packages ; do
    echo "pip install $pkg..."
    $SUDO $PYTHON -m pip install "$pkg" --user "$USER"
done
