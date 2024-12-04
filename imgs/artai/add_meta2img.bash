#!/bin/bash

# Verifica si se proporcionó un nombre de archivo
if [ "$#" -ne 1 ]; then
    echo "Uso: $0 nombre_de_la_imagen.jpg"
    exit 1
fi

# Solicita al usuario que ingrese los metadatos
read -p "Ingrese el comentario: " COMENTARIO
read -p "Ingrese el autor: " AUTOR
read -p "Ingrese el título: " TITULO

# Agregar metadatos a la imagen
exiftool -overwrite_original \
-Comment="$COMENTARIO" \
-Author="$AUTOR" \
-Title="$TITULO" \
"$1"
