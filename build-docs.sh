#!/bin/bash
# Script para atualizar a documentação do Crescent Framework

echo "🌙 Crescent Framework - Documentation Builder"
echo "=============================================="
echo ""

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale o Python 3 primeiro."
    exit 1
fi

echo "📝 Convertendo arquivos Markdown para HTML..."
python3 convert-docs.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Documentação gerada com sucesso!"
    echo ""
    echo "📄 Arquivo gerado: docs.html"
    echo "📏 Tamanho: $(du -h docs.html | cut -f1)"
    echo ""
    echo "🌐 Para visualizar:"
    echo "   open docs.html          # macOS"
    echo "   xdg-open docs.html      # Linux"
    echo "   start docs.html         # Windows"
    echo ""
    echo "🚀 Para publicar:"
    echo "   git add docs/ docs.html convert-docs.py"
    echo "   git commit -m 'docs: atualizar documentação'"
    echo "   git push origin main"
else
    echo ""
    echo "❌ Erro ao gerar documentação"
    exit 1
fi
