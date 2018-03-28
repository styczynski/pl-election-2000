[![Made by Styczynsky Digital Systems][badge sts]][link styczynski]

[![Screenshot of webpage][screenshot1]](http://styczynski.in/pl-election-2000)

# 📜 📊 Quick static site generator and remastered voting site

  The purpose of this project completed as an assignment for 3W subject was to design Python3 compatible static site generator using Jinja2 template engine. Then using this self-written engine generate remastered version of polish presidental elections site.
  
The original site is available at:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Presidental elections 2000](http://prezydent2000.pkw.gov.pl/wb/wb.html)

The remake is available at:

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[http://styczynski.in/pl-election-2000](http://styczynski.in/pl-election-2000)

## Requirements

This projects requires bash shell (or at least some kind of emulation) and Python 3.

## Setup

  The generator performs auto-configuration and then run server at localhost:8000 with autoreload.
  To begin just type the following command into the bash shell:
  ```
  
  ./generate up
  
  ```
  
  Then wait for completion and navigate to `localhost:8000/build/index.html` to see the results.
  
  **Please note:** in `generate` file you must specify python executable you are using (if it's not default *python* or *python3*)
  
## Advanced setup

  You can manually configure you virtual environment or use your global one:
  Execute the following command to install all requirements:
  
  ```
    pip install -r requirements.txt
  ```
  
## Generator commands

 Generator script `generate` supports the following commands:
 
 * **init**
 
          Automatically create virtual environment for execution
          Skip if it actually exists.
 * **reset**
 
          Automatically create virtual environment for execution
          Override any previous one.
 * **build**
 
          Build static site.
          Output files to ./build
 * **server** (alias: **dev**)
 
          Run static server at localhost:8000 with auto rebuild
 * **release**
 
          Prepare release-ready version of files
 * **up**
 
          Alias for executing setup and then server command
 
## How does it work?
 
Generate script loads main page and subpages form subfolders of templates folders:
  * Firstly it generates DataGenerator from index.py if it exists
  * Then creates index.html from index.html Jinja2-compatible template
  * Copies needed index.css/index.js files mangling them as Jinja templates
  * These steps are repeated for all folders inside templates directory (if the index.html/.py/.css etc. is placed inside `templates/<dir>` then the generated subpage is named `<dir>.html`
  
Let's assume we call main index.html and subpages' index'es as single **page**.
 
For each **page** index.html is required anything to be generated.<br>
But index.js/.css/.py are optional.
 
If the index.py is not provided then template is rendered with no data.
 
If the index.py is provided then it must define the following class:
 
```python

class DataGenerator:

    def __init__(self, path, config, globalGenerator):
       # ...

    def getFileNames(self):
        # ...

    def prepareData(self, data, fileName, fileIndex):
        # ...
 
```

### __init__(self, path, config, globalGenerator)

The DataGenerator contructor is invoked when the render occurs.<br>
`path` - path to the rendered .html template
`config` - generator configuration
`globalGenerator` - generator for top-level index.html (for index.html generator that argument is None, because the generator is not yet created)

### getFileNames(self)

Optional method that returns array of the files that generator should generate instead of default subpage page.<br>
Example:

```python

def getFileNames(self):
        return [ 'override' ];

```

If the generator is placed inside `templates/subpage` directory then only `subpage_override.html` file will be generated.

*Note:* Top-level generator cannot generate anything more than 'index.html' so this method has no effect there.

### prepareData(self, data, fileName, fileIndex)

`data` - initial data (data inherited from generator configuration and top-level index generator)
`fileName` - file to be generated (`'default'` when getFileNames method was not defined; elements of getFileNames() otherwise)
`fileIndex` - index of current file on the list of all files that will be generated (files are indexed from 0)

The method is required and should return data object with added keys.<br>
The entire returned data object will be available when rendering files.

[![Screenshot of webpage][screenshot2]](http://styczynski.in/pl-election-2000)

[badge sts]: https://img.shields.io/badge/-styczynsky_digital_systems-blue.svg?style=flat-square&logoWidth=20&logo=data%3Aimage%2Fpng%3Bbase64%2CiVBORw0KGgoAAAANSUhEUgAAABYAAAAXCAYAAAAP6L%2BeAAAABmJLR0QA%2FwD%2FAP%2BgvaeTAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAB3RJTUUH4AgSEh0nVTTLngAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAm0lEQVQ4y2Pc%2Bkz2PwMNAAs2wVMzk4jSbJY%2BD6ccEwONACMsKIh1JSEgbXKeQdr4PO1cPPQMZiGkoC7bkCQD7%2Fx7znDn35AOClK9PEJSBbNYAJz999UGrOLocsM0KHB5EZ%2FXPxiVMDAwMDD8SP3DwJA6kFka5hJCQOBcDwMDAwPDm3%2FbGBj%2BbR8tNrFUTbiAB8tknHI7%2FuTilAMA9aAwA8miDpgAAAAASUVORK5CYII%3D

[link styczynski]: http://styczynski.in

[screenshot1]: https://raw.githubusercontent.com/styczynski/pl-election-2000/master/static/screenshot.png

[screenshot2]: https://raw.githubusercontent.com/styczynski/pl-election-2000/master/static/screenshot2.png

