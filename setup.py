import setuptools

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

# Read requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="TurnVoice",
    version="0.0.65",
    author="Kolja Beigel",
    author_email="kolja.beigel@web.de",
    description="Replaces and translates voices in youtube videos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KoljaB/TurnVoice",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'turnvoice=turnvoice.core.turnvoice:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=requirements,
    package_data={'RealtimeTTS': ['engines/*.json']},
    include_package_data=True,
    keywords='replace, voice, youtube, video, audio, voice, synthesis, '
             'sentence-segmentation, TTS-engine, audio-playback, '
             'stream-player, sentence-fragment, audio-feedback, '
             'interactive, python'
)
