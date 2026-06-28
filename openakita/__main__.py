"""CLI 入口"""
import sys
from .main import OpenAkita


def main():
    akita = OpenAkita()
    akita.run()


if __name__ == "__main__":
    main()