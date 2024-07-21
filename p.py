from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from instagrapi import Client
import re
import logging

app = FastAPI()

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Credenciais do Instagram
IG_USERNAME = "juliadofreee00"
IG_PASSWORD = "LUANLEVY20"

# Inicializa o cliente do Instagram e faz login
cl = Client()
cl.login(IG_USERNAME, IG_PASSWORD)

def extract_shortcode(url: str) -> str:
    """Extrai o shortcode da URL do Instagram."""
    logger.info(f"Extraindo shortcode da URL: {url}")
    
    # Regex para capturar o shortcode da URL
    match = re.search(r'/reel/([^/]+)/|/p/([^/]+)/', url)
    if match:
        shortcode = match.group(1) or match.group(2)
        logger.info(f"Shortcode extraído: {shortcode}")
        return shortcode
    raise ValueError("URL inválida.")

@app.get("/instagram/video")
async def get_video(url: str):
    try:
        logger.info(f"Recebido pedido para baixar vídeo: {url}")
        shortcode = extract_shortcode(url)
        logger.info(f"Obtendo informações da mídia para shortcode: {shortcode}")

        media_pk = cl.media_pk_from_code(shortcode)  # Conversão do shortcode para media_pk
        
        # Usar métodos públicos e privados para obter informações
        try:
            media = cl.media_info_gql(media_pk)
        except Exception as e:
            logger.error(f"Erro ao usar método gql: {e}")
            media = cl.media_info_v1(media_pk)
        
        if media is None:
            raise HTTPException(status_code=404, detail="Mídia não encontrada.")
        
        if media.media_type != 2:
            raise HTTPException(status_code=400, detail="A URL fornecida não é um vídeo.")
        
        # Baixar o vídeo
        file_path = cl.video_download(media_pk)
        logger.info(f"Caminho do arquivo baixado: {file_path}")
        
        # Servir o arquivo diretamente ao usuário
        return FileResponse(str(file_path), media_type='video/mp4', filename=file_path.name)
    except ValueError as e:
        logger.error(f"Erro ao extrair shortcode: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao baixar mídia: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor: " + str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)