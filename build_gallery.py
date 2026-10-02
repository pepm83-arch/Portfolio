import os
import glob
import json

base_dir = r"C:\Users\Josep\Documents\GitHub\Portfolio"
html_file = os.path.join(base_dir, "index.html")

extensions = ('*.png', '*.jpg', '*.jpeg', '*.mp4', '*.mov')
files = []
for ext in extensions:
    files.extend(glob.glob(os.path.join(base_dir, '**', ext), recursive=True))

projects = {}
for f in files:
    rel_path = os.path.relpath(f, base_dir).replace('\\', '/')
    if rel_path == "index.html" or rel_path.endswith('.py'): continue
    
    parts = rel_path.split('/')
    
    if parts[0] == "Props_stopmotion":
        group_key = "Props_stopmotion"
        project_name = "Props Stop Motion"
    elif parts[0] == "Motion_Graphics":
        group_key = parts[0] + "/" + parts[1].split('.')[0]
        project_name = parts[1].split('.')[0]
    else:
        group_key = os.path.dirname(rel_path)
        project_name = os.path.basename(group_key)
        
    if group_key not in projects:
        projects[group_key] = {"name": project_name.replace('_', ' ').title(), "items": []}
    projects[group_key]["items"].append(rel_path)

gallery_html = ""
for group_key, data in projects.items():
    project_name = data["name"]
    items = data["items"]
    
    # Ordenar para que los .mp4 y .mov sean los primeros
    items.sort(key=lambda x: not (x.lower().endswith('.mp4') or x.lower().endswith('.mov')))
    
    cover_item = items[0]
    
    if "tiburon" in group_key.lower():
        for item in items:
            if "render4" in item.lower():
                cover_item = item
                break
            
    cat_id = "all"
    subtitle = "Proyecto 3D"
    lower_path = group_key.lower()
    
    if "monumentos_falleros" in lower_path:
        cat_id = "fallas"
        subtitle = "Monumento Fallero"
    elif "envoirment" in lower_path or "entornos" in lower_path:
        cat_id = "entornos"
        subtitle = "Entornos y Escenarios"
    elif "esculpido" in lower_path or "tiburon" in lower_path:
        cat_id = "figuras"
        subtitle = "Escultura / Figuras"
    elif "props_stopmotion" in lower_path:
        cat_id = "props"
        subtitle = "Props Stop Motion"
        project_name = "Colección de Props"
    elif "motion_graphics" in lower_path:
        cat_id = "motion"
        subtitle = "Motion Graphics"
    elif "animacion" in lower_path:
        cat_id = "animacion"
        subtitle = "Animación"
    elif "concept_art" in lower_path:
        cat_id = "concept"
        subtitle = "Concept Art"

    items_json = json.dumps(items)
    
    is_video = cover_item.lower().endswith(('.mp4', '.mov'))
    if is_video:
        media_html = f'<video autoplay loop muted playsinline class="w-full h-auto"><source src="{cover_item}"></video>'
    else:
        media_html = f'<img loading="lazy" src="{cover_item}" alt="{project_name}" class="w-full h-auto object-cover">'
        
    gallery_html += f"""
    <div class="masonry-item {cat_id} cursor-pointer" data-category="{cat_id}" onclick='openModal({items_json}, "{project_name}")'>
        {media_html}
        <div class="overlay">
            <h3 class="text-xl font-bold text-center px-2">{project_name}</h3>
            <p class="mt-2 text-sm text-gray-300">{subtitle}</p>
            <div class="mt-4 border border-white px-4 py-1 rounded-full text-xs font-bold bg-white/20 backdrop-blur-sm">
                Ver {len(items)} archivos
            </div>
        </div>
    </div>
    """

html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>José Miguel Martínez | Monfosc Studio</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap');
        body {{ font-family: 'Inter', sans-serif; background-color: #f9f9f9; color: #111; }}
        
        .masonry-grid {{ column-count: 1; column-gap: 1.5rem; }}
        @media (min-width: 640px) {{ .masonry-grid {{ column-count: 2; }} }}
        @media (min-width: 1024px) {{ .masonry-grid {{ column-count: 3; }} }}
        @media (min-width: 1536px) {{ .masonry-grid {{ column-count: 4; }} }}
        
        .masonry-item {{
            break-inside: avoid; margin-bottom: 1.5rem; position: relative; border-radius: 8px; overflow: hidden;
            background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        .masonry-item:hover {{ transform: translateY(-5px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); }}
        
        .overlay {{
            position: absolute; inset: 0; background: rgba(0,0,0,0.7); color: white; opacity: 0;
            display: flex; align-items: center; justify-content: center; flex-direction: column; transition: opacity 0.3s ease;
        }}
        .masonry-item:hover .overlay {{ opacity: 1; }}
        .filter-btn.active {{ background-color: #111; color: #fff; }}

        #modal-gallery-container::-webkit-scrollbar {{ width: 8px; }}
        #modal-gallery-container::-webkit-scrollbar-track {{ background: #111; }}
        #modal-gallery-container::-webkit-scrollbar-thumb {{ background: #333; border-radius: 4px; }}
    </style>
</head>
<body class="antialiased">

    <!-- Modal para ver proyecto completo -->
    <div id="project-modal" class="fixed inset-0 z-[100] bg-black/95 hidden flex flex-col">
        <div class="flex justify-between items-center p-6 border-b border-gray-800">
            <h2 id="modal-title" class="text-2xl font-bold text-white uppercase tracking-wider">Proyecto</h2>
            <button onclick="closeModal()" class="text-gray-400 hover:text-white transition-colors">
                <i class="fa-solid fa-xmark text-3xl"></i>
            </button>
        </div>
        <div id="modal-gallery-container" class="flex-1 overflow-y-auto p-6 md:p-12">
            <div id="modal-gallery" class="max-w-5xl mx-auto space-y-8 flex flex-col items-center">
            </div>
        </div>
    </div>

    <!-- Navbar -->
    <nav class="fixed w-full z-50 bg-white/90 backdrop-blur-md border-b border-gray-200">
        <div class="max-w-screen-2xl mx-auto px-6 lg:px-12">
            <div class="flex items-center justify-between h-20">
                <div class="font-black text-2xl tracking-tighter uppercase flex items-center gap-2">
                    <i class="fa-solid fa-cube text-black"></i> MONFOSC<span class="text-gray-400 font-light">STUDIO</span>
                </div>
                <div class="hidden md:flex items-center space-x-8 font-semibold text-sm">
                    <a href="#portfolio" class="hover:text-blue-600 transition-colors">PORTFOLIO</a>
                    <a href="#cv" class="hover:text-blue-600 transition-colors">SOBRE MÍ & CV</a>
                    <a href="https://monfosc.com/" target="_blank" class="hover:text-blue-600 transition-colors">WEB OFICIAL</a>
                    <a href="https://cults3d.com/es/usuarios/Monfosc_Studio/modelos-3d" target="_blank" class="bg-blue-600 text-white px-5 py-2.5 rounded-full hover:bg-blue-700 transition-colors">
                        TIENDA CULTS3D
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Header -->
    <header class="pt-40 pb-20 px-6 lg:px-12 max-w-screen-2xl mx-auto">
        <div class="max-w-4xl">
            <h1 class="text-6xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8">
                JOSÉ MIGUEL. <br>
                <span class="text-gray-400">3D ARTIST &</span> <br>
                <span class="text-blue-600">MODELER.</span>
            </h1>
            <p class="text-xl md:text-2xl text-gray-600 font-light max-w-2xl mb-10 leading-relaxed">
                Especialista en modelado 3D, diseño de props, escenarios y monumentos falleros. Fundador de <strong>Monfosc Studio</strong>.
            </p>
            <div class="flex flex-wrap gap-4">
                <a href="#portfolio" class="bg-black text-white px-8 py-4 rounded-full font-bold hover:bg-gray-800 transition-colors text-lg">Ver {len(projects)} Proyectos</a>
                <a href="#contacto" class="border-2 border-black text-black px-8 py-4 rounded-full font-bold hover:bg-gray-100 transition-colors text-lg">Contactar</a>
            </div>
        </div>
    </header>

    <section id="portfolio" class="px-6 lg:px-12 max-w-screen-2xl mx-auto mb-8">
        <div class="flex flex-wrap gap-3 border-b border-gray-200 pb-6">
            <button class="filter-btn active px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="all">Todos ({len(projects)})</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="figuras">Figuras</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="fallas">Fallas</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="props">Props</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="entornos">Entornos</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="animacion">Animación</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="concept">Concept Art</button>
            <button class="filter-btn bg-white text-black hover:bg-gray-100 px-6 py-2 rounded-full border border-gray-300 font-medium text-sm transition-colors" data-filter="motion">Motion</button>
        </div>
    </section>

    <section class="px-6 lg:px-12 max-w-screen-2xl mx-auto mb-24">
        <div class="masonry-grid" id="gallery">
            {gallery_html}
        </div>
    </section>

    <section id="cv" class="bg-black text-white py-24">
        <div class="max-w-screen-2xl mx-auto px-6 lg:px-12">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-16">
                <div class="col-span-1">
                    <h2 class="text-4xl font-black tracking-tighter mb-6">SOBRE MÍ</h2>
                    <p class="text-gray-400 font-light text-lg mb-8 leading-relaxed">
                        Soy José Miguel, profesional del 3D con formación multidisciplinar. Combino el arte tradicional con las nuevas tecnologías para crear assets de videojuegos, monumentos falleros y figuras para impresión.
                    </p>
                    <div class="space-y-4">
                        <p><i class="fa-solid fa-envelope w-8 text-gray-500"></i> Pepm83@gmail.com</p>
                        <p><i class="fa-brands fa-artstation w-8 text-gray-500"></i> <a href="https://www.artstation.com/pepm83" class="hover:text-blue-400">ArtStation Profile</a></p>
                        <p><i class="fa-solid fa-globe w-8 text-gray-500"></i> <a href="https://monfosc.com/" class="hover:text-blue-400">Monfosc.com</a></p>
                    </div>
                </div>

                <div class="col-span-1 lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div>
                        <h3 class="text-2xl font-bold mb-6 text-blue-500 border-b border-gray-800 pb-2">Experiencia Laboral</h3>
                        <ul class="space-y-6">
                            <li><h4 class="font-bold text-lg">Modelador 3D Props y Escenarios</h4><p class="text-gray-400 text-sm">Inspira Animation</p></li>
                            <li><h4 class="font-bold text-lg">Modelador de Fallas</h4><p class="text-gray-400 text-sm">Sacabutx Art S.L.</p></li>
                            <li><h4 class="font-bold text-lg">Diseñador Gráfico Freelance</h4><p class="text-gray-400 text-sm">Logotipos y maquetación</p></li>
                            <li><h4 class="font-bold text-lg">Profesor y Coordinador</h4><p class="text-gray-400 text-sm">Fundación Secretariado Gitano / Colevisa S.L.</p></li>
                        </ul>
                    </div>
                    <div>
                        <h3 class="text-2xl font-bold mb-6 text-blue-500 border-b border-gray-800 pb-2">Formación Académica</h3>
                        <ul class="space-y-6">
                            <li><h4 class="font-bold text-lg">CFGS Animación 3D y Entornos Interactivos</h4></li>
                            <li><h4 class="font-bold text-lg">Máster en Creación Digital e Innovación</h4><p class="text-gray-400 text-sm">Nuevas Tecnologías</p></li>
                            <li><h4 class="font-bold text-lg">Concept Art y Stop Motion</h4><p class="text-gray-400 text-sm">RTVE / Inspira Animation</p></li>
                            <li><h4 class="font-bold text-lg">Magisterio y Téc. Ortoprotésico</h4></li>
                        </ul>
                    </div>
                    <div class="md:col-span-2 mt-6">
                        <h3 class="text-2xl font-bold mb-6 text-blue-500 border-b border-gray-800 pb-2">Herramientas y Skills</h3>
                        <div class="flex flex-wrap gap-3">
                            <span class="bg-gray-800 px-4 py-2 rounded font-medium text-sm">Blender</span>
                            <span class="bg-gray-800 px-4 py-2 rounded font-medium text-sm">ZBrush</span>
                            <span class="bg-gray-800 px-4 py-2 rounded font-medium text-sm">Substance Painter</span>
                            <span class="bg-gray-800 px-4 py-2 rounded font-medium text-sm">Unity</span>
                            <span class="bg-gray-800 px-4 py-2 rounded font-medium text-sm">Adobe Suite</span>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <footer id="contacto" class="bg-[#f9f9f9] py-32 text-center">
            <h2 class="text-5xl md:text-7xl font-black tracking-tighter mb-8">¿TRABAJAMOS JUNTOS?</h2>
            <a href="mailto:Pepm83@gmail.com" class="text-2xl md:text-4xl font-light hover:text-blue-600 transition-colors border-b-2 border-black hover:border-blue-600 pb-2">
                Pepm83@gmail.com
            </a>
            <div class="mt-20 flex justify-center gap-8 text-3xl">
                <a href="https://monfosc.com/" class="text-gray-400 hover:text-black transition-colors"><i class="fa-solid fa-globe"></i></a>
                <a href="https://cults3d.com/es/usuarios/Monfosc_Studio/modelos-3d" class="text-gray-400 hover:text-black transition-colors"><i class="fa-solid fa-cube"></i></a>
                <a href="https://www.artstation.com/pepm83" class="text-gray-400 hover:text-black transition-colors"><i class="fa-brands fa-artstation"></i></a>
            </div>
            <p class="mt-12 text-gray-500 text-sm">© 2026 José Miguel M. | Monfosc Studio</p>
        </footer>

        <script>
            function openModal(images, title) {{
                const modal = document.getElementById('project-modal');
                const gallery = document.getElementById('modal-gallery');
                document.getElementById('modal-title').innerText = title;
                
                gallery.innerHTML = '';
                images.forEach(src => {{
                    const lowerSrc = src.toLowerCase();
                    if(lowerSrc.endsWith('.mp4') || lowerSrc.endsWith('.mov')) {{
                        gallery.innerHTML += `<video controls autoplay loop muted playsinline class="w-full max-w-4xl rounded-lg shadow-2xl mb-4"><source src="${{src}}"></video>`;
                    }} else {{
                        gallery.innerHTML += `<img src="${{src}}" class="w-full max-w-4xl rounded-lg shadow-2xl mb-4">`;
                    }}
                }});
                
                modal.classList.remove('hidden');
                document.body.style.overflow = 'hidden';
            }}
            
            function closeModal() {{
                document.getElementById('project-modal').classList.add('hidden');
                document.getElementById('modal-gallery').innerHTML = ''; 
                document.body.style.overflow = 'auto';
            }}

            document.addEventListener('DOMContentLoaded', () => {{
                const filterBtns = document.querySelectorAll('.filter-btn');
                const items = document.querySelectorAll('.masonry-item');

                filterBtns.forEach(btn => {{
                    btn.addEventListener('click', () => {{
                        filterBtns.forEach(b => {{
                            b.classList.remove('active', 'bg-black', 'text-white');
                            b.classList.add('bg-white', 'text-black');
                        }});
                        
                        btn.classList.remove('bg-white', 'text-black');
                        btn.classList.add('active', 'bg-black', 'text-white');

                        const filter = btn.getAttribute('data-filter');

                        items.forEach(item => {{
                            if (filter === 'all' || item.getAttribute('data-category') === filter) {{
                                item.style.display = 'block';
                            }} else {{
                                item.style.display = 'none';
                            }}
                        }});
                    }});
                }});
            }});
        </script>
    </body>
    </html>
"""

with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_template)
