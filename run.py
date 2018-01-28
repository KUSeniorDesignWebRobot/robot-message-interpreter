from security import Security


def main():

    sec = Security()
    sec.generate_cert()
    sec.run()


if __name__ == "__main__":
    main()
