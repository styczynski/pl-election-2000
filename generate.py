from jinja2 import Environment,PackageLoader,FileSystemLoader
from jinja2 import select_autoescape
import importlib
import shutil
import pathlib
import os

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

templatesEntrypoints = {}
templatePathsList = os.listdir(TEMPLATES_DIRECTORY)

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
        print('[i] Prepare global data...')
        templateConfigModule = importlib.import_module(f'{TEMPLATES_PACKAGE}.index')
        templateDataPrepared = templateConfigModule.prepareData(templateData)
        if templateDataPrepared is not None:
            templateData = templateDataPrepared
        print('[i] Save global data...')

    templatesEntrypoints[f'index.html'] = {
        'output': f'{OUTPUT_DIRECTORY}/index.html',
        'configPy': None,
        'inputJS': templatesEntrypointsJS,
        'inputCSS': templatesEntrypointsCSS,
        'outputJS': f'{OUTPUT_DIRECTORY}/index.js',
        'outputCSS': f'{OUTPUT_DIRECTORY}/index.css'
    }

 #for sectionName in AUTO_GENERATED_SECTIONS:
 #   print(f'[?] Look for auto-generated section {sectionName}.tmpl...')
 #   if os.path.isfile(f'{TEMPLATES_DIRECTORY}/{sectionName}.tmpl'):
 #       print('    * Found!')
 #       jinjaEnv = Environment(
 #           loader=FileSystemLoader(TEMPLATES_DIRECTORY),
 #           autoescape=select_autoescape(['html', 'xml'])
 #       )
 #       template = jinjaEnv.get_template(f'{sectionName}.tmpl')
 #       templateParameters = {**templateData, **templateParametersPredefined}
 #       templateParametersPredefined[sectionName] = template.render(**templateParameters)
 #   else:
 #       templateParametersPredefined[sectionName] = ''

pathlib.Path(OUTPUT_DIRECTORY).mkdir(parents=True, exist_ok=True)

print(f'[i] Found {len(templatesEntrypoints)} subpage/-s templates.')

print('[i] Generate templates...')
for templateInputPath, templateConfig in templatesEntrypoints.items():
    templateOutputPath = templateConfig['output']
    templateConfigPy = templateConfig['configPy']
    templateConfigModule = None

    if templateConfigPy is not None:
        templateConfigModule = importlib.import_module(templateConfigPy)

    print(f'    * Generate template {templateInputPath} -> {templateOutputPath}')
    jinjaEnv = Environment(
        loader=FileSystemLoader(TEMPLATES_DIRECTORY),
        autoescape=select_autoescape(['html','xml'])
    )

    templateParameters = {**templateData, **templateParametersPredefined}

    if templateConfigModule is not None:
        print(f'        - Prepare data for template')
        templateParametersPrepared = templateConfigModule.prepareData(templateParameters)
        if templateParametersPrepared is not None:
            templateParameters = templateParametersPrepared
        print(f'        - Save data for template')

    template = jinjaEnv.get_template(templateInputPath)
    with open(templateOutputPath, 'wb') as out:
        out.write(
            template.render(**templateParameters).encode('utf-8')
        )

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

print('[i] DONE.')