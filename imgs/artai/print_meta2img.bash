#!/bin/bash

# Verifica si se proporcionó un nombre de archivo
if [ "$#" -ne 1 ]; then
    echo "Uso: $0 nombre_de_la_imagen.jpg"
    exit 1
fi

# Agregar metadatos a la imagen
exiftool -Author -Copyright -Title -Comment "$1"

