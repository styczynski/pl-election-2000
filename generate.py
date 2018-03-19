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

templateData = {
    'generatorVersion': config['GENERATOR_VERSION']
}

templateParametersPredefined = {
    'templates': f'../{config["TEMPLATES_DIRECTORY"]}',
    'assets': './assets',
    'vendor': './vendor'
}

def renderSubtemplate(templateOutputPathForSubfile, template, templateDataGenerator, templateParameters, templateDataFilename, indexNo):
    templateParametersForSubfile = templateParameters

    templateParametersPrepared = templateDataGenerator.prepareData(templateParameters, templateDataFilename, indexNo)
    if templateParametersPrepared is not None:
        templateParametersForSubfile = templateParametersPrepared

    with open(templateOutputPathForSubfile, 'wb') as out:
        out.write(
            template.render(**templateParametersForSubfile).encode('utf-8')
        )

def subtemplateMapping(propsList):

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

    #for i in pool.imap_unordered(f, range(3)):
    #    print(i)

    #pool.imap_unordered(subtemplateMapping, subtemplatesArgs)
    #bar.finish()


def generateTemplates():
    start_time = datetime.now()

    pool = Pool(7)

    global templateData
    global templateParametersPredefined

    templatesEntrypoints = {}
    templatePathsList = os.listdir(config['TEMPLATES_DIRECTORY'])

    #try:

    templateGlobalDataGenerator = None

    print(f'[?] Look for templates inside {config["TEMPLATES_DIRECTORY"]}')
    bar = Bar(f'Searching directories...', max=len(templatePathsList))

    for templatePath in templatePathsList:
        if os.path.isdir(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}'):
            if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.html') or os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/{templatePath}/index.py'):
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
                    'output': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.html',
                    'outputPrefix': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}',
                    'outputPostfix': f'.html',
                    'configPy': templatesEntrypointsConfigPy,
                    'inputJS': templatesEntrypointsJS,
                    'inputCSS': templatesEntrypointsCSS,
                    'outputJS': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.js',
                    'outputCSS': f'{config["OUTPUT_DIRECTORY"]}/{templatePath}.css'
                }
        bar.next()
    bar.finish()

    if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.html'):
        templatesEntrypointsConfigPy = None
        templatesEntrypointsJS = None
        templatesEntrypointsCSS = None

        if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.js'):
            templatesEntrypointsJS = f'index.js'

        if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.css'):
            templatesEntrypointsCSS = f'index.css'

        if os.path.isfile(f'{config["TEMPLATES_DIRECTORY"]}/index.py'):
            #templatesEntrypointsConfigPy = f'{TEMPLATES_PACKAGE}.index'
            #templateData
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
            'output': f'{config["OUTPUT_DIRECTORY"]}/index.html',
            'outputPrefix': f'{config["OUTPUT_DIRECTORY"]}/index',
            'outputPostfix': f'.html',
            'configPy': None,
            'inputJS': templatesEntrypointsJS,
            'inputCSS': templatesEntrypointsCSS,
            'outputJS': f'{config["OUTPUT_DIRECTORY"]}/index.js',
            'outputCSS': f'{config["OUTPUT_DIRECTORY"]}/index.css'
        }

    pathlib.Path(config['OUTPUT_DIRECTORY']).mkdir(parents=True, exist_ok=True)

    print(f'[i] Found {len(templatesEntrypoints)} subpage/-s templates.')


    print('[i] Generate templates...')
    for templateID, templateConfig in templatesEntrypoints.items():
        templateInputPath = templateConfig['input']
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

        if templateConfigModule is not None:
            print(f'        - Load DataGenerator...')
            templateDataGenerator = templateConfigModule.DataGenerator(templateInputPath, config, templateGlobalDataGenerator)
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

            renderSubtemplates(pool, templateID, templateOutputPrefix, templateOutputPostfix,
                               templateInputPath, templateDataGenerator, templateParameters)

            #templateDataFilenames = templateDataGenerator.getFileNames()
            #indexNo = 0

            #bar = Bar(f'Processing template {templateID}', max=len(templateDataFilenames))

            #subtemplatesArgs = []

            #
            # renderSubtemplate(templateDataFilenames, templateOutputPrefix, templateOutputPostfix, template, templateDataGenerator, templateParameters, templateDataFilename, indexNo)

            #
            #for templateDataFilename in templateDataFilenames:
            #    templateParametersForSubfile = templateParameters
            #    templateOutputPathForSubfile = f'{templateOutputPrefix}_{templateDataFilename}{templateOutputPostfix}'
            #    renderSubtemplate(templateOutputPathForSubfile, template, templateDataGenerator, templateParameters, templateDataFilename, indexNo)
            #    indexNo = indexNo + 1
            #    #if indexNo % 50 == 0:
            #    bar.next()
            #bar.finish()

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
    #except:
    #    print(f'[!] Unexpected error: {sys.exc_info()[0]}')

    time_elapsed = datetime.now() - start_time
    pool.close()
    print('[#] Done in (hh:mm:ss.ms) {}'.format(time_elapsed))


def loadCliParameters():
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

if __name__ == "__main__":
    runCli()