# Contributing to Inmanta

Hello, and welcome! Whether you are looking for help, reporting a bug,
thinking about contributing to the module or about to submit a patch, this
document is for you!

## Where to seek help?

Opening a pull request in this repository is the main channel used by the
community and Inmanta.
We also have a bunch of videos on YouTube that you can use to get up to speed with Inmanta using [this link](https://www.youtube.com/watch?v=l_ClsJG-BNQ&list=PL8UgC-AkgG7ZfqzTBpBYh_Uiou8SsjHaW).

## Contributing

We welcome your contributions of any kind. Feel free to contribute fixes or features,
If you are asked to update your patch/feature by a reviewer, please do so! Remember:
**you are responsible for pushing your PR forward**.

If your Pull Request was accepted, congratulations!
You are now an official contributor to Inmanta. [Get in touch with us](code@inmanta.com) to receive
a special gift.

### Writing tests

We use [pytest](https://docs.pytest.org/en/7.1.x/contents.html) to write our tests. Your PR should include the related test updates or additions, in the appropriate test suite.
Checkout the existing ones, for instance [interface](/tests/test_interface.py) to get a head start.

#### Commit atomicity

When submitting PRs, it is important that you organize your commits in
logical units of work. You are free to propose a patch/feature with one or many
commits, as long as their atomicity is respected. This means that no unrelated
changes should be included in a commit.

Writing meaningful commit messages will also help the maintainer who is reviewing your PR.
