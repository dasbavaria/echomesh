apt-get install\
 ffmpeg\
 freeglut3-dev\
 git\
 libasound2-dev\
 libasound2-dev\
 libfreetype6-dev\
 libjack-dev\
 libx11-dev\
 libxcomposite-dev\
 libxcursor-dev\
 libxinerama-dev\
 locate\
 mesa-common-dev\
 mpg123\
 oss-compat\
 python-httplib2\
 python-imaging\
 python-pyaudio\
 python2.7-dev\
&&\
\
pushd /tmp &&\
rm -Rf /tmp/py-spidev &&\
git clone git://github.com/doceme/py-spidev &&\
cd /tmp/py-spidev &&\
python setup.py install &&\
popd &&\
rm -Rf /tmp/py-spidev &&\
echo "Raspberry Pi libraries installation completed."
