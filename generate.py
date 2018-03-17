from jinja2 import Environment,PackageLoader,FileSystemLoader
from jinja2 import select_autoescape
import importlib
import shutil
import pathlib
import time
import os
import webbrowser
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import FileSystemEventHandler
from bin.static_server import *


GENERATOR_VERSION = '1.0.0'

OUTPUT_DIRECTORY = './build'
TEMPLATES_DIRECTORY = './templates'
TEMPLATES_PACKAGE = 'templates'
VENDOR_DIRECTORY = './vendor'
ASSETS_DIRECTORY = './assets'

#AUTO_GENERATED_SECTIONS = ['header', 'footer']

templateData = {
    'generatorVersion': GENERATOR_VERSION
}

templateParametersPredefined = {
    'templates': f'../{TEMPLATES_DIRECTORY}',
    'assets': './assets',
    'vendor': './vendor'
}

lastGenerationTrigger = time.time()

def generateTemplates():

    global templateData
    global templateParametersPredefined
    global lastGenerationTrigger

    #if time.time() - lastGenerationTrigger <= 10:
    #    print('[.] Supress generation trigger.')
    #    return

    lastGenerationTrigger = time.time()

    templatesEntrypoints = {}
    templatePathsList = os.listdir(TEMPLATES_DIRECTORY)

    try:

        print(f'[?] Look for templates inside {TEMPLATES_DIRECTORY}')
        for templatePath in templatePathsList:
            if os.path.isdir(f'{TEMPLATES_DIRECTORY}/{templatePath}'):
                if os.path.isfile(f'{TEMPLATES_DIRECTORY}/{templatePath}/index.html'):
                    templatesEntrypointsConfigPy = None
                    templatesEntrypointsJS = None
                    templatesEntrypointsCSS = None

                    if os.path.isfile(f'{TEMPLATES_DIRECTORY}/{templatePath}/index.py'):
                        templatesEntrypointsConfigPy = f'{TEMPLATES_PACKAGE}.{templatePath}.index'

                    if os.path.isfile(f'{TEMPLATES_DIRECTORY}/{templatePath}/index.js'):
                        templatesEntrypointsJS = f'{templatePath}/index.js'

                    if os.path.isfile(f'{TEMPLATES_DIRECTORY}/{templatePath}/index.css'):
                        templatesEntrypointsCSS = f'{templatePath}/index.css'

                    templatesEntrypoints[f'{templatePath}/index.html'] = {
                        'output': f'{OUTPUT_DIRECTORY}/{templatePath}.html',
                        'outputPrefix': f'{OUTPUT_DIRECTORY}/{templatePath}',
                        'outputPostfix': f'.html',
                        'configPy': templatesEntrypointsConfigPy,
                        'inputJS': templatesEntrypointsJS,
                        'inputCSS': templatesEntrypointsCSS,
                        'outputJS': f'{OUTPUT_DIRECTORY}/{templatePath}.js',
                        'outputCSS': f'{OUTPUT_DIRECTORY}/{templatePath}.css'
                    }

        if os.path.isfile(f'{TEMPLATES_DIRECTORY}/index.html'):
            templatesEntrypointsConfigPy = None
            templatesEntrypointsJS = None
            templatesEntrypointsCSS = None

            if os.path.isfile(f'{TEMPLATES_DIRECTORY}/index.js'):
                templatesEntrypointsJS = f'index.js'

            if os.path.isfile(f'{TEMPLATES_DIRECTORY}/index.css'):
                templatesEntrypointsCSS = f'index.css'

            if os.path.isfile(f'{TEMPLATES_DIRECTORY}/index.py'):
                #templatesEntrypointsConfigPy = f'{TEMPLATES_PACKAGE}.index'
                #templateData
                print('[i] Prepare global DataGenerator...')

                templateConfigModule = importlib.import_module(f'{TEMPLATES_PACKAGE}.index')
                templateConfigModule = importlib.reload(templateConfigModule)

                templateGlobalDataGenerator = templateConfigModule.DataGenerator(f'{TEMPLATES_DIRECTORY}/index.html')

                templateDataPrepared = templateGlobalDataGenerator.prepareData(templateData, 'default', 0)
                if templateDataPrepared is not None:
                    templateData = templateDataPrepared

                print('[i] Save global DataGenerator...')

            templatesEntrypoints[f'index.html'] = {
                'output': f'{OUTPUT_DIRECTORY}/index.html',
                'outputPrefix': f'{OUTPUT_DIRECTORY}/index',
                'outputPostfix': f'.html',
                'configPy': None,
                'inputJS': templatesEntrypointsJS,
                'inputCSS': templatesEntrypointsCSS,
                'outputJS': f'{OUTPUT_DIRECTORY}/index.js',
                'outputCSS': f'{OUTPUT_DIRECTORY}/index.css'
            }

        pathlib.Path(OUTPUT_DIRECTORY).mkdir(parents=True, exist_ok=True)

        print(f'[i] Found {len(templatesEntrypoints)} subpage/-s templates.')


        print('[i] Generate templates...')
        for templateInputPath, templateConfig in templatesEntrypoints.items():
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
                loader=FileSystemLoader(TEMPLATES_DIRECTORY),
                autoescape=select_autoescape(['html','xml'])
            )

            templateParameters = {**templateData, **templateParametersPredefined}

            templateDataGenerator = None

            if templateConfigModule is not None:
                print(f'        - Load DataGenerator...')
                templateDataGenerator = templateConfigModule.DataGenerator(templateInputPath)
                print(f'        - Loaded DataGenerator')

            template = jinjaEnv.get_template(templateInputPath)

            if templateDataGenerator is None:
                with open(templateOutputPath, 'wb') as out:
                    out.write(
                        template.render(**templateParameters).encode('utf-8')
                    )
            elif not hasattr(templateDataGenerator, 'getFileNames'):
                templateParametersPrepared = templateDataGenerator.prepareData(templateParameters, 'default', 0)
                if templateParametersPrepared is not None:
                    templateParameters = templateParametersPrepared

                with open(templateOutputPath, 'wb') as out:
                    out.write(
                        template.render(**templateParameters).encode('utf-8')
                    )
            else:
                templateDataFilenames = templateDataGenerator.getFileNames()
                indexNo = 0

                for templateDataFilename in templateDataFilenames:
                    templateParametersForSubfile = templateParameters
                    templateOutputPathForSubfile = f'{templateOutputPrefix}_{templateDataFilename}{templateOutputPostfix}'
                    templateParametersPrepared = templateDataGenerator.prepareData(templateParameters, templateDataFilename, indexNo)
                    if templateParametersPrepared is not None:
                        templateParametersForSubfile = templateParametersPrepared
                    with open(templateOutputPathForSubfile, 'wb') as out:
                        out.write(
                            template.render(**templateParametersForSubfile).encode('utf-8')
                        )
                    indexNo = indexNo+1


            if (templateConfig['inputJS'] is not None) and (templateConfig['outputJS'] is not None):
                print(f'        - Generate JS')
                template = jinjaEnv.get_template(templateConfig['inputJS'])
                print(f'        - Save JS')
                with open(templateConfig['outputJS'], 'wb') as out:
                    out.write(
                        template.render(**templateParameters).encode('utf-8')
                    )

            if (templateConfig['inputCSS'] is not None) and (templateConfig['outputCSS'] is not None):
                print(f'        - Generate CSS')
                template = jinjaEnv.get_template(templateConfig['inputCSS'])
                print(f'        - Save CSS')
                with open(templateConfig['outputCSS'], 'wb') as out:
                    out.write(
                        template.render(**templateParameters).encode('utf-8')
                    )
    except:
        print(f'[!] Unexpected error: {sys.exc_info()[0]}')


generateTemplates()

if not os.path.isdir(f'{OUTPUT_DIRECTORY}/vendor'):
    print('[i] Copy vendor files...')
    shutil.copytree(VENDOR_DIRECTORY, f'{OUTPUT_DIRECTORY}/vendor')
else:
    print('[i] Vendor files present.')

if not  os.path.isdir(f'{OUTPUT_DIRECTORY}/assets'):
    print('[i] Copy assets files...')
    shutil.copytree(ASSETS_DIRECTORY, f'{OUTPUT_DIRECTORY}/assets')
else:
    print('[i] Assets files present.')

print('[i] Generation DONE.')

server = AsyncServer()
server.start()

class FileChangedHandler(FileSystemEventHandler):
    def on_modified(self, event):
        generateTemplates()

event_handler = FileChangedHandler()
observer = Observer()
observer.schedule(event_handler, path=TEMPLATES_DIRECTORY, recursive=True)
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