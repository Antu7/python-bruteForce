# Simple Brute Force Attack Tools Using Python


## Simple Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requests and argparse.

```bash
pip install requests
pip install argparse
```

## Run

### `interactive` mode

```bash
python3 bruteforce.py -i
```

### Normal mode

To see help page:
```bash
python3 bruteforce.py -h
```

#### Arguments

Note: Arguments with `--` prefix are optional and they are not necessary

Argument name | argument type | description | example
------------- | ------------- | ----------- | -------
`url` | Website URL | URL to page on website to which POST request is made while logging in | `http://127.0.0.1/login.php`
`username` | Text | Correct username for attacked account | `admin`
`error` | Text | Content of error message which is displayed when wrong password is entered | `Wrong password`
`--login-field` | Text | Name of login field in POST request (more in POST Requests) | `login_field`
`--password-field` | Text | Name of password field in POST request (more in POST Requests) | `password_field`
`--threads` | Number | Number of threads (processes) to run at the same time | `2`
`--passwords-file` | File path | Path to file with passwords list | `dicts/small-passwords.txt`

## More about BruteForce attacks

For more please check this Medium [Link](https://medium.com/@textmeantu/brute-force-attack-with-python-c1d70fcba607)
 
## Example

![alt text](https://raw.githubusercontent.com/Antu7/python-bruteForce/master/test_example.jpg)

For more password List check This [Git Repo](https://github.com/Antu7/password-generator)

## POST Requests

POST Request is made to website server when you click "Log In" button. To see details about this request open `Developer Options` in your browser and navigate to `Network` tab. Then press "Log In" button and find row corresponding to POST request that was made. When you click it, you can see information about `request` and `response`. In `request` tab find name of fields that were send. You can see how to do this on `test_website` in the video below.

ADD VIDEO!

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
