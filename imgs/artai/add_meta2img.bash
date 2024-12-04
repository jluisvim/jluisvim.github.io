#!/bin/bash

# Verifica si se proporcionó un nombre de archivo
if [ "$#" -ne 1 ]; then
    echo "Uso: $0 nombre_de_la_imagen.jpg"
    exit 1
fi

# Definir los datos importantes
AUTOR="jlvm"
COPYRIGHT="© 2024 jlvm"

# Solicita al usuario que ingrese los metadatos
read -p "Ingrese el comentario: " COMENTARIO
read -p "Ingrese el título: " TITULO

# Agregar metadatos a la imagen
exiftool -overwrite_original \
-Author="$AUTOR" \
-Copyright="$COPYRIGHT" \
-Title="$TITULO" \
-Comment="$COMENTARIO" \
"$1"

if [ $? -eq 0 ]; then
    echo "Metadatos agregados correctamente."
else
    echo "Error al agregar metadatos."
fi
