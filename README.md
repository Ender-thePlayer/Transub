# Transub
A simple translator for *.srt and *.ass files.

# Installation

Use the [flatpak-builder](https://pip.pypa.io/en/stable/) to build and install transub.

## Ubuntu / Debian
```bash
sudo apt-get install flatpak-builder
```

## Fedora
```bash
sudo dnf install flatpak-builder
```



# Build And Install the app
```bash
flatpak install flathub org.gnome.Platform//44 org.gnome.Sdk//44
flatpak-builder --user --install --force-clean build-dir org.stardev.Transub.yml
```
```bash
flatpak run org.stardev.Transub
```

