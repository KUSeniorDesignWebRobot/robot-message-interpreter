from CommandMessageManager import commandMessageManager
from ManifestReader import ManifestReader
import config


def main():
    manifest = ManifestReader(config.MANIFEST_FILENAME).getManifest()
    commandMessageManager(manifest)


if __name__ == "__main__":
    main()
