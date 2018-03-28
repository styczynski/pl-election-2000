
#########################################
#  Fast pythonic static site generator  #
#########################################

#
#
#   Static site generator needs at least Python 3.
#
#    Usage:
#        ./generate <mode>
#
#        Whre mode is:
#            init
#                Automatically create virtual environment for execution
#                Skip if it actually exists.
#
#            reset
#                Automatically create virtual environment for execution
#                Override any previous one.
#
#            build
#                Build static site.
#                Output files to ./build
#
#            server [alias: dev]
#                Run static server at localhost:8000 with auto rebuild
#
#            release
#                Prepare release-ready version of files
#
#            up
#                Alias for executing setup and then server command
#
#
#  Piotr Styczyński @styczynski
#  March 2018 MIT LICENSE
#
#

from jinja2 import Environment,PackageLoader,FileSystemLoader
from jinja2 import select_autoescape
import importlib
import shutil
import pathlib
import time
import os
import sys
from multiprocessing import Pool
import webbrowser
from datetime import datetime
from progress.bar import Bar
from jsmin import jsmin
from html5print import HTMLBeautifier
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from bin.static_server import *

config = {
    'MODE': 'build',
    'DEPLOY_URL': 'http://localhost:8000/build',
    'GENERATOR_VERSION': '1.0.0',
    'OUTPUT_DIRECTORY': './build',
    'TEMPLATES_DIRECTORY': './templates',
    'TEMPLATES_PACKAGE': 'templates',
    'VENDOR_DIRECTORY': './vendor',
    'ASSETS_DIRECTORY': './assets'
}
"""
    Global generator configuration.
"""

templateData = {
    'generatorVersion': config['GENERATOR_VERSION']
}
"""
    Default data for templates.
"""

templateParametersPredefined = {
    'templates': f'../{config["TEMPLATES_DIRECTORY"]}',
    'assets': './assets',
    'vendor': './vendor'
}

MODE = config['MODE']
"""
    Default mode (default mode is saved under config['MODE'])
"""

def renderSubtemplate(templateOutputPathForSubfile, template, templateDataGenerator, templateParameters, templateDataFilename, indexNo):
    """
        Generates one of the HTML templates listed by DataGenerator.
    """
    templateParametersForSubfile = templateParameters

    templateParametersPrepared = templateDataGenerator.prepareData(templateParameters, templateDataFilename, indexNo)
    if templateParametersPrepared is not None:
        templateParametersForSubfile = templateParametersPrepared

    with open(templateOutputPathForSubfile, 'wb') as out:
        out.write(
            HTMLBeautifier.beautify(template.render(**templateParametersForSubfile), 4).encode('utf-8')
        )

def subtemplateMapping(propsList):
    """
        Generates one of the HTML templates listed by DataGenerator.
        This function can be mapped onto the property list of valid format.
        (see renderSubtemplates for more details)
    """

    template = None

    for props in propsList:

        templateOutputPathForSubfile = props['templateOutputPathForSubfile']
        indexNo = props['indexNo']
        templateInputPath = props['templateInputPath']
        templateDataGenerator = props['templateDataGenerator']
        templateParameters = props['templateParameters']
        templateDataFilename = props['templateDataFilename']

        if template is None:
            jinjaEnv = Environment(
                loader=FileSystemLoader(config['TEMPLATES_DIRECTORY']),
                autoescape=select_autoescape(['html', 'xml'])
            )
            template = jinjaEnv.get_template(templateInputPath)

        renderSubtemplate(templateOutputPathForSubfile, template, templateDataGenerator, templateParameters,
                          templateDataFilename, indexNo)

    return True

def renderSubtemplates(pool, templateID, templateOutputPrefix, templateOutputPostfix,
                       templateInputPath, templateDataGenerator, templateParameters):
    """
        Generates templates for given data generator.
    """
    
                       
    templateDataFilenames = templateDataGenerator.getFileNames()
    indexNo = 0

    subtemplatesArgs = [ ]

    for templateDataFilename in templateDataFilenames:
        templateOutputPathForSubfile = f'{templateOutputPrefix}_{templateDataFilename}{templateOutputPostfix}'
        subtemplatesArgs.append({
            'templateOutputPathForSubfile': templateOutputPathForSubfile,
            'indexNo': indexNo,
            'templateDataFilename': templateDataFilename,
            'templateInputPath': templateInputPath,
            'templateDataGenerator': templateDataGenerator,
            'templateParameters': templateParameters
        })
        indexNo = indexNo + 1

    subtemplatesArgsChunked = []
    chunkSize = 40
    for i in range(0, len(subtemplatesArgs), chunkSize):
        subtemplatesArgsChunked.append(subtemplatesArgs[i:i + chunkSize])

    bar = Bar(f'Processing template {templateID}', max=len(subtemplatesArgsChunked)*chunkSize)
    for i in pool.imap_unordered(subtemplateMapping, subtemplatesArgsChunked):
        for j in range(chunkSize):
            bar.next()

    bar.finish()


def generateTemplates():
    """
        Generate all templates.
    """
    global MODE
    start_time = datetime.now()

    pool = Pool(7)

    global templateData
    global templateParametersPredefined

    templatesEntrypoints = {}
    templatePathsList = os.listdir(config['TEMPLATES_DIRECTORY'])

    try:

      templateGlobalDataGenerator = None

      print(f'[?] Look for templates inside {config["TEMPLATES_DIRECTORY"]}')
      bar = Bar(f'Searching directories...', max=len(templatePathsList))

      for templatePath in templatePathsList:
          if os.path.isdir(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}'):
              if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.html') or os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.py'):
                  #
                  # This loop tries to find all html/js/css/py files.
                  #
                  
                  templatesEntrypointsConfigPy = None
                  templatesEntrypointsJS = None
                  templatesEntrypointsCSS = None

                  if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.py'):
                      templatesEntrypointsConfigPy = f'{config["TEMPLATES_PACKAGE"]}.{templatePath}.index'

                  if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.js'):
                      templatesEntrypointsJS = f'{templatePath}/index.js'

                  if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.css'):
                      templatesEntrypointsCSS = f'{templatePath}/index.css'

                  templateInputPath = f'{templatePath}/index.html'

                  if not os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.html'):
                      if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.html'):
                          templateInputPath = 'index.html'

                  templatesEntrypoints[f'{templatePath}/index.html'] = {
                      'input': templateInputPath,
                      'inputLocation': f'{templatePath}',
                      'output': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.html',
                      'outputPrefix': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}',
                      'outputPostfix': f'.html',
                      'isGlobal': False,
                      'configPy': templatesEntrypointsConfigPy,
                      'inputJS': templatesEntrypointsJS,
                      'inputCSS': templatesEntrypointsCSS,
                      'outputJS': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.js',
                      'outputJSPrefix': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}_',
                      'outputJSPostfix': f'.js',
                      'outputCSS': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.css'
                  }
          bar.next()
      bar.finish()

      #
      # Find global top-level css/js/html/py file.
      #
      if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.html'):
          templatesEntrypointsConfigPy = None
          templatesEntrypointsJS = None
          templatesEntrypointsCSS = None

          if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.js'):
              templatesEntrypointsJS = f'index.js'

          if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.css'):
              templatesEntrypointsCSS = f'index.css'

          if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.py'):
              print('[i] Prepare global DataGenerator...')
              
              templateConfigModule = importlib.import_module(f'{config["TEMPLATES_PACKAGE"]}.index')
              templateConfigModule = importlib.reload(templateConfigModule)

              templateGlobalDataGenerator = templateConfigModule.DataGenerator(f'{config["TEMPLATES_DIRECTORY"]}/index.html', config)

              templateDataPrepared = templateGlobalDataGenerator.prepareData(templateData, 'default', 0)
              if templateDataPrepared is not None:
                  templateData = templateDataPrepared

              print('[i] Save global DataGenerator...')

          templatesEntrypoints[f'index.html'] = {
              'input': 'index.html',
              'inputLocation': f'.',
              'output': f'{config["OUTPUT_DIRECTORY"]}/index.html',
              'outputPrefix': f'{config["OUTPUT_DIRECTORY"]}/index',
              'outputPostfix': f'.html',
              'configPy': None,
              'isGlobal': True,
              'inputJS': templatesEntrypointsJS,
              'inputCSS': templatesEntrypointsCSS,
              'outputJS': f'{config["OUTPUT_DIRECTORY"]}/index.js',
              'outputJSPrefix': f'{config["OUTPUT_DIRECTORY"]}/',
              'outputJSPostfix': f'.js',
              'outputCSS': f'{config["OUTPUT_DIRECTORY"]}/index.css'
          }

      pathlib.Path(config['OUTPUT_DIRECTORY']).mkdir(parents=True, exist_ok=True)

      print(f'[i] Found {len(templatesEntrypoints)} subpage/-s templates.')

        
      print('[i] Generate templates...')
      for templateID, templateConfig in templatesEntrypoints.items():
          templateInputPath = templateConfig['input']
          templateInputLocation = templateConfig['inputLocation']
          templateOutputPath = templateConfig['output']
          templateOutputPrefix = templateConfig['outputPrefix']
          templateOutputPostfix = templateConfig['outputPostfix']
          templateConfigPy = templateConfig['configPy']
          templateConfigModule = None

          if templateConfigPy is not None:
              templateConfigModule = importlib.import_module(templateConfigPy)
              templateConfigModule = importlib.reload(templateConfigModule)

          print(f'    * Generate template {templateInputPath} -> {templateOutputPath}')
          jinjaEnv = Environment(
              loader=FileSystemLoader(config['TEMPLATES_DIRECTORY']),
              autoescape=select_autoescape(['html','xml'])
          )

          templateParameters = {**templateData, **templateParametersPredefined}

          templateDataGenerator = None
          generatorScoped = None
          
          if templateConfigModule is not None:
              print(f'        - Load DataGenerator...')
              templateDataGenerator = templateConfigModule.DataGenerator(templateInputPath, config, templateGlobalDataGenerator)
              print(f'        - Loaded DataGenerator')

          generatorScoped = templateDataGenerator
          if templateConfig['isGlobal']:
              generatorScoped = templateGlobalDataGenerator
              
          template = jinjaEnv.get_template(templateInputPath)

          if templateDataGenerator is None:
              with open(templateOutputPath, 'wb') as out:
                  out.write(
                      HTMLBeautifier.beautify(template.render(**templateParameters), 4).encode('utf-8')
                  )
          elif not hasattr(templateDataGenerator, 'getFileNames'):
              templateParametersPrepared = templateDataGenerator.prepareData(templateParameters, 'default', 0)
              if templateParametersPrepared is not None:
                  templateParameters = templateParametersPrepared

              with open(templateOutputPath, 'wb') as out:
                  out.write(
                      HTMLBeautifier.beautify(template.render(**templateParameters), 4).encode('utf-8')
                  )
          else:

              renderSubtemplates(pool, templateID, templateOutputPrefix, templateOutputPostfix,
                                 templateInputPath, templateDataGenerator, templateParameters)

                                 
                                 
          if ((templateConfig['inputJS'] is not None) and (templateConfig['outputJS'] is not None)) or (hasattr(templateDataGenerator, 'getJSFileNames')):
              
              JSfilelist = []
              
              
              if ((templateConfig['inputJS'] is not None) and (templateConfig['outputJS'] is not None)):
                JSfilelist = [
                    {
                        'name': 'default',
                        'input':  templateConfig['inputJS'],
                        'output': templateConfig['outputJS']
                    }
                ]
              
              if hasattr(generatorScoped, 'getJSFileNames'):
                  print('        - Detected additional JS modules')
                  JSNames = generatorScoped.getJSFileNames()
                  for name in JSNames:
                      JSfilelist.append({
                          'name': name,
                          'input': f'{templateInputLocation}/{name}.js',
                          'output': f'{templateConfig["outputJSPrefix"]}{name}{templateConfig["outputJSPostfix"]}'
                      })
              
              
              for JSFile in JSfilelist:
              
                  outputJS = JSFile["output"]
                  inputJS = JSFile["input"]
                  name = JSFile["name"]
              
                  print(f'        - Generating JS module: {name}...')
                  template = jinjaEnv.get_template(inputJS)
                  print(f'            -> Render module')
                  renderedModule = template.render(**templateParameters)
                  
                  with open(outputJS, 'wb') as out:
                      if MODE is 'release':
                          print(f'            -> Minify JS module')
                          out.write(
                              jsmin(renderedModule).encode('utf-8')
                          )
                      else:
                          print(f'            -> Save JS module')
                          out.write(
                              (renderedModule).encode('utf-8')
                          )

          if (templateConfig['inputCSS'] is not None) and (templateConfig['outputCSS'] is not None):
              print(f'        - Generate CSS...')
              template = jinjaEnv.get_template(templateConfig['inputCSS'])
              print(f'        - Save CSS...')
              with open(templateConfig['outputCSS'], 'wb') as out:
                  out.write(
                      template.render(**templateParameters).encode('utf-8')
                  )
    except:
        print(f'[!] Unexpected error: {sys.exc_info()[0]}')

    time_elapsed = datetime.now() - start_time
    pool.close()
    print('[#] Done in (hh:mm:ss.ms) {}'.format(time_elapsed))


def loadCliParameters():
    """
        Sets configuration reading argv variables.
    """
    global MODE
    if len(sys.argv) > 1:
        if (sys.argv[1] == 'dev') or (sys.argv[1] == 'server'):
            print('[i] Running in live dev server mode.')
            print('[i] ...')
            MODE = 'server'
        elif (sys.argv[1] == 'build'):
            MODE = 'build'
        elif (sys.argv[1] == 'release'):
            print('[i] Release mode.')
            MODE = 'release'
            print("[i] You must enter deploy url.")
            print("[i] It's the url you service will be available at.")
            print("[i] For example enter: abc.com/page if you want to access abc.com/page/index.html")
            config['DEPLOY_URL'] = input("[>] Deploy url: ").strip('/')
        else:
            print("""
    Usage:
        ./generate <mode>

        Whre mode is:
            build
                Build static site.
                Output files to ./build

            server [alias: dev]
                Run static server at localhost:8000 with auto rebuild

            release
                Prepare release-ready version of files

            """)
            sys.exit(1)

def runCli():
    """
        Runs generator in command line interface mode (interactive).
    """
    global MODE
    loadCliParameters()
    generateTemplates()

    if not os.path.isdir(f'{config["OUTPUT_DIRECTORY"]}/vendor'):
        print('[i] Copy vendor files...')
        shutil.copytree(config['VENDOR_DIRECTORY'], f'{config["OUTPUT_DIRECTORY"]}/vendor')
    else:
        print('[i] Vendor files present.')

    if not  os.path.isdir(f'{config["OUTPUT_DIRECTORY"]}/assets'):
        print('[i] Copy assets files...')
        shutil.copytree(config['ASSETS_DIRECTORY'], f'{config["OUTPUT_DIRECTORY"]}/assets')
    else:
        print('[i] Assets files present.')

    print('[i] Generation DONE.')

    if MODE is not 'server':
        print('[#] Not in server mode so terminate...')
        sys.exit()

    server = AsyncServer()
    server.start()

    class FileChangedHandler(FileSystemEventHandler):
        def on_modified(self, event):
            generateTemplates()

    event_handler = FileChangedHandler()
    observer = Observer()
    observer.schedule(event_handler, path=config['TEMPLATES_DIRECTORY'], recursive=True)
    observer.start()

    webbrowser.open('http://localhost:8000/build/index.html')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
    server.join()

    print('[i] Terminate main worker...')

# The default behaviour is to start CLI mode
if __name__ == "__main__":
    runCli()