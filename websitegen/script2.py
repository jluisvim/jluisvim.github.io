import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from datetime import datetime
import webbrowser
from threading import Thread

class NewsScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Consultor de Noticias")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        # Configuración de fuentes de noticias
        self.news_sources = {
            "BBC Mundo": {
                "url": "https://www.bbc.com/mundo", 
                "selectors": {
                    "article": "div[class*='gs-c-promo']",
                    "title": "h3",
                    "summary": "p[class*='gs-c-promo-summary']",
                    "date": "time",
                    "link": "a"
                },
                "categories": {
                    "Portada": "",
                    "Internacional": "world",
                    "Ciencia": "science_and_environment",
                    "Tecnología": "technology"
                }
            },
            "El País": {
                "url": "https://elpais.com", 
                "selectors": {
                    "article": "article",
                    "title": "h2",
                    "summary": "p",
                    "date": "time",
                    "link": "a"
                },
                "categories": {
                    "Portada": "",
                    "Internacional": "internacional",
                    "Tecnología": "tecnologia",
                    "Cultura": "cultura"
                }
            },
            "CNN Español": {
                "url": "https://cnnespanol.cnn.com", 
                "selectors": {
                    "article": "article",
                    "title": "h2",
                    "summary": "div.post-excerpt",
                    "date": "span.post-date",
                    "link": "a"
                },
                "categories": {
                    "Portada": "",
                    "Mundo": "category/mundo",
                    "Salud": "category/salud",
                    "Tecnología": "category/tecnologia"
                }
            }
        }
        self.create_widgets()
        self.current_news = []

    def create_widgets(self):
        # Frame superior para controles
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        # Selector de fuente
        ttk.Label(control_frame, text="Fuente:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_var = tk.StringVar()
        self.source_combobox = ttk.Combobox(
            control_frame, 
            textvariable=self.source_var, 
            values=list(self.news_sources.keys()),
            state="readonly"
        )
        self.source_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.source_combobox.current(0)
        self.source_combobox.bind("<<ComboboxSelected>>", self.update_categories)
        # Botones para gestionar fuentes
        ttk.Button(
            control_frame, 
            text="Agregar Fuente", 
            command=self.add_source
        ).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(
            control_frame, 
            text="Editar Fuente", 
            command=self.edit_source
        ).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(
            control_frame, 
            text="Eliminar Fuente", 
            command=self.remove_source
        ).grid(row=0, column=4, padx=5, pady=5)
        # Selector de categoría
        ttk.Label(control_frame, text="Categoría:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.category_var = tk.StringVar()
        self.category_combobox = ttk.Combobox(
            control_frame, 
            textvariable=self.category_var,
            state="readonly"
        )
        self.category_combobox.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        # Botón de búsqueda
        self.search_button = ttk.Button(
            control_frame, 
            text="Buscar Noticias", 
            command=self.start_scraping_thread
        )
        self.search_button.grid(row=1, column=2, padx=5, pady=5)
        # Barra de progreso
        self.progress = ttk.Progressbar(
            control_frame, 
            orient=tk.HORIZONTAL, 
            mode='indeterminate'
        )
        self.progress.grid(row=2, column=0, columnspan=5, sticky=tk.EW, pady=5)
        # Frame principal para resultados
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        # Lista de noticias
        self.news_listbox = tk.Listbox(
            main_frame, 
            height=15,
            selectmode=tk.SINGLE,
            font=('Arial', 10)
        )
        self.news_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.news_listbox.bind('<<ListboxSelect>>', self.show_news_detail)
        self.news_listbox.bind('<Double-Button-1>', self.open_news_url)
        # Detalle de la noticia seleccionada
        self.news_detail = scrolledtext.ScrolledText(
            main_frame, 
            wrap=tk.WORD,
            font=('Arial', 10),
            height=10,
            state='disabled'
        )
        self.news_detail.pack(fill=tk.BOTH, expand=True)
        # Frame inferior para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        # Botón para abrir noticia en navegador
        self.open_button = ttk.Button(
            button_frame, 
            text="Abrir en Navegador", 
            command=self.open_news_url,
            state='disabled'
        )
        self.open_button.pack(side=tk.LEFT, padx=5)
        # Botón para guardar resultados
        ttk.Button(
            button_frame, 
            text="Guardar Resultados", 
            command=self.save_results
        ).pack(side=tk.RIGHT, padx=5)
        # Actualizar categorías al inicio
        self.update_categories()

    def add_source(self):
        name = simpledialog.askstring("Agregar Fuente", "Nombre de la Fuente:")
        if name and name not in self.news_sources:
            url = simpledialog.askstring("Agregar Fuente", "URL de la Fuente:")
            if url:
                self.news_sources[name] = {
                    "url": url,
                    "selectors": {},
                    "categories": {}
                }
                self.update_combobox_values()
                self.source_combobox.set(name)
                messagebox.showinfo("Éxito", f"La fuente '{name}' ha sido agregada.")
        else:
            messagebox.showwarning("Advertencia", "El nombre de la fuente ya existe o es inválido.")

    def edit_source(self):
        name = self.source_var.get()
        if name:
            new_name = simpledialog.askstring("Editar Fuente", "Nuevo Nombre:", initialvalue=name)
            if new_name:
                new_url = simpledialog.askstring("Editar Fuente", "Nueva URL:", initialvalue=self.news_sources[name]['url'])
                if new_url:
                    self.news_sources[new_name] = self.news_sources.pop(name)
                    self.news_sources[new_name]['url'] = new_url
                    self.update_combobox_values()
                    self.source_combobox.set(new_name)
                    messagebox.showinfo("Éxito", f"La fuente '{name}' ha sido editada a '{new_name}'.")
        else:
            messagebox.showwarning("Advertencia", "Por favor selecciona una fuente para editar.")

    def remove_source(self):
        name = self.source_var.get()
        if name:
            confirm = messagebox.askyesno("Eliminar Fuente", f"¿Estás seguro de eliminar '{name}'?")
            if confirm:
                del self.news_sources[name]
                self.update_combobox_values()
                if self.news_sources:
                    self.source_combobox.set(next(iter(self.news_sources)))
                messagebox.showinfo("Éxito", f"La fuente '{name}' ha sido eliminada.")
        else:
            messagebox.showwarning("Advertencia", "Por favor selecciona una fuente para eliminar.")

    def update_combobox_values(self):
        self.source_combobox['values'] = list(self.news_sources.keys())

    def update_categories(self, event=None):
        """Actualiza las categorías disponibles según la fuente seleccionada"""
        source = self.source_var.get()
        if source in self.news_sources:
            categories = self.news_sources[source]["categories"]
            self.category_combobox['values'] = list(categories.keys())
            self.category_combobox.current(0)

    def start_scraping_thread(self):
        """Inicia el scraping en un hilo separado para no bloquear la GUI"""
        self.progress.start()
        self.search_button['state'] = 'disabled'
        self.news_listbox.delete(0, tk.END)
        self.news_detail.config(state='normal')
        self.news_detail.delete(1.0, tk.END)
        self.news_detail.config(state='disabled')
        thread = Thread(target=self.scrape_news)
        thread.start()
        self.root.after(100, self.check_thread, thread)

    def check_thread(self, thread):
        """Verifica si el hilo de scraping ha terminado"""
        if thread.is_alive():
            self.root.after(100, self.check_thread, thread)
        else:
            self.progress.stop()
            self.search_button['state'] = 'normal'

    def scrape_news(self):
        """Obtiene las noticias de la fuente seleccionada"""
        source_name = self.source_var.get()
        category_name = self.category_var.get()
        if not source_name:
            messagebox.showerror("Error", "Por favor selecciona una fuente de noticias")
            return
        source = self.news_sources[source_name]
        category_path = source["categories"].get(category_name, "")
        try:
            url = source["url"]
            if category_path:
                url = f"{url}/{category_path}" if not url.endswith("/") else f"{url}{category_path}"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            selectors = source["selectors"]
            articles = soup.select(selectors["article"])
            self.current_news = []
            for article in articles[:15]:  # Limitar a 15 artículos
                try:
                    title_elem = article.select_one(selectors["title"])
                    title = title_elem.get_text(strip=True) if title_elem else "Sin título"
                    link_elem = article.select_one(selectors["link"])
                    if link_elem and 'href' in link_elem.attrs:
                        link = link_elem['href']
                        if not link.startswith('http'):
                            link = f"{source['url']}{link}" if not source['url'].endswith('/') else f"{source['url']}{link[1:]}"
                    else:
                        link = ""
                    summary_elem = article.select_one(selectors["summary"]) if "summary" in selectors else None
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""
                    date_elem = article.select_one(selectors["date"]) if "date" in selectors else None
                    date = date_elem.get_text(strip=True) if date_elem else ""
                    if title and link:  # Solo agregar si tiene título y enlace
                        news_item = {
                            "title": title,
                            "link": link,
                            "summary": summary,
                            "date": date,
                            "source": source_name,
                            "category": category_name
                        }
                        self.current_news.append(news_item)
                        # Actualizar la lista en la GUI (debe hacerse en el hilo principal)
                        self.root.after(0, self.update_news_list, news_item)
                except Exception as e:
                    print(f"Error procesando artículo: {e}")
                    continue
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Error", f"No se pudo obtener las noticias: {str(e)}")

    def update_news_list(self, news_item):
        """Actualiza la lista de noticias en la GUI"""
        self.news_listbox.insert(tk.END, news_item["title"])

    def show_news_detail(self, event):
        """Muestra el detalle de la noticia seleccionada"""
        selection = self.news_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if 0 <= index < len(self.current_news):
            news = self.current_news[index]
            self.news_detail.config(state='normal')
            self.news_detail.delete(1.0, tk.END)
            self.news_detail.insert(tk.END, f"Título: {news['title']}", 'title')

            self.news_detail.insert(tk.END, f"Fuente: {news['source']}", 'source')
            self.news_detail.insert(tk.END, f"Categoría: {news['category']}", 'category')
            if news['date']:
                self.news_detail.insert(tk.END, f"Fecha: {news['date']}", 'date')
            else:
                self.news_detail.insert(tk.END, "", 'date')
            if news['summary']:
                self.news_detail.insert(tk.END, f"Resumen:{news['summary']}", 'summary')
            self.news_detail.insert(tk.END, f"Enlace: {news['link']}", 'link')
            # Configurar estilos
            self.news_detail.tag_config('title', font=('Arial', 12, 'bold'))
            self.news_detail.tag_config('source', foreground='blue')
            self.news_detail.tag_config('category', foreground='green')
            self.news_detail.tag_config('date', foreground='gray')
            self.news_detail.tag_config('summary', font=('Arial', 10))
            self.news_detail.tag_config('link', foreground='blue', underline=True)
            self.news_detail.config(state='disabled')
            self.open_button['state'] = 'normal'

    def open_news_url(self, event=None):
        """Abre la noticia seleccionada en el navegador web"""
        selection = self.news_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        if 0 <= index < len(self.current_news):
            webbrowser.open_new_tab(self.current_news[index]["link"])

    def save_results(self):
        """Guarda las noticias en un archivo de texto"""
        if not self.current_news:
            messagebox.showwarning("Advertencia", "No hay noticias para guardar")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"noticias_{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== CONSULTA DE NOTICIAS ===")
                f.write(f"Fuente: {self.source_var.get()}")
                f.write(f"Categoría: {self.category_var.get()}")
                f.write(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                f.write(f"Total de noticias: {len(self.current_news)}")
                for i, news in enumerate(self.current_news, 1):
                    f.write(f"=== NOTICIA {i} ===")
                    f.write(f"Título: {news['title']}")
                    f.write(f"Fuente: {news['source']}")
                    f.write(f"Categoría: {news['category']}")
                    if news['date']:
                        f.write(f"Fecha: {news['date']}")
                    if news['summary']:
                        f.write(f"Resumen: {news['summary']}")
                    f.write(f"Enlace: {news['link']}")
            messagebox.showinfo("Éxito", f"Las noticias se han guardado en {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NewsScraperGUI(root)
    root.mainloop()
