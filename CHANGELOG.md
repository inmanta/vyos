# Changelog

## v3.0.10 - ?


## v3.0.9 - 2024-07-12


## v3.0.8 - 2024-07-05


## v3.0.7 - 2024-03-29


## v3.0.6 - 2023-10-12


## v3.0.5 - 2023-06-30


## v3.0.4 - 2023-05-08

- Convert constraints in requirements.txt file
- Added `null` defaults to nullable attributes. These attributes can now only be set in the constructor.

# V2.0.1
- Fix VLAN ID type constraint

# V2.0.0
- Change bridge config from bridge-group to members for vyos>1.2.6

# V1.3.9
- Replace cleanup fixture

# V1.3.8
- Remove pytest.ini and move its logic to pyproject.toml

# V1.3.7
- Add pytest.ini file and set asyncio_mode to auto

# V1.3.6
- Added examples

# v1.3.4
- Update inmanta-dev-dependencies package

# v1.3.3
- Allow slightly different configuration save confirmation message for ubiquiti devices (#29)

# V1.3.2
- Use inmanta-dev-dependencies package

# V1.3.1
- Fix test cases

# V1.3.0
- Added the option to skip resources when host connection fails (#90)

# V1.2.1
- Improved error reporting

# V1.2.0
- Ensure connection failure always results in an error

# V1.1.3
- Added missing dev dependency (#20)

# V1.1.2
- Fixed purge dependencies for policy based routing (#41)

# V1.1.1
- Added table to index on StaticRoute
