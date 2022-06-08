# VyOS Module

Open-source module to configure [VyOS](https://vyos.io/) network devices.

## Usage

In order to get started with using this module, we have prepared a bunch of YouTube videos to walk you through the entire process. The links to these videos are mentioned below.

1. [OSPF configuration - Flat model](https://www.youtube.com/watch?v=ak_r9wpBE-Q)
2. [OSPF configuration - Enhanced model](https://www.youtube.com/watch?v=LBOpezx8UwI)
3. [Contributing to VyOS module - OSPFv3](https://www.youtube.com/watch?v=4VI65buWdXM)

## Running tests

`Python 3.9+` is required to run tests. If your system does not ship with that version installed, [pyenv](https://github.com/pyenv/pyenv) can be used to install additional Python versions.

1. Create a virtual environment:

    ```bash
    python3.9 -m venv ~/.virtualenvs/vyos
    ```

2. Install the dependencies:

    ```bash
    source ~/.virtualenvs/vyos/bin/activate
    pip install -r requirements.txt
    pip install -r requirements.dev.txt
    ```

3. Set up the test environment by following [this guide](https://github.com/inmanta/examples/tree/master/Networking/Vyos).

4. Make a clean-slate configuration file by connecting to the `VyOS` device and running the following command:

    ```console
    configure
    save /config/clear.config
    ```

    > This `clear.config` file is used in the tests to automatically clear the configuration, avoiding potential conflicts.

5. Run the tests:

    ```bash
    export VY_TEST_HOST="10.11.12.100"
    pytest tests
    ```

## Contributing

All contributions are welcome by following [this guide](CONTRIBUTING.md). We have a [video](https://www.youtube.com/watch?v=4VI65buWdXM) for that as well!
