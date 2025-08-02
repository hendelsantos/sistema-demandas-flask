"""
Script para migrar demandas existentes e adicionar campos anuais.
Execute este script APÓS fazer as modificações no modelo Demanda.
"""

from app import app, db, Demanda
from datetime import datetime

def migrar_demandas_existentes():
    """
    Migra demandas existentes adicionando:
    - ano_orcamentario baseado na data_criacao
    - numero_demanda sequencial por ano
    """
    with app.app_context():
        print("Iniciando migração de demandas existentes...")
        
        # Buscar todas as demandas sem ano_orcamentario
        demandas_sem_ano = Demanda.query.filter(
            (Demanda.ano_orcamentario.is_(None)) | 
            (Demanda.numero_demanda.is_(None))
        ).order_by(Demanda.data_criacao).all()
        
        print(f"Encontradas {len(demandas_sem_ano)} demandas para migrar...")
        
        # Agrupar por ano para gerar números sequenciais
        demandas_por_ano = {}
        
        for demanda in demandas_sem_ano:
            ano = demanda.data_criacao.year
            if ano not in demandas_por_ano:
                demandas_por_ano[ano] = []
            demandas_por_ano[ano].append(demanda)
        
        # Processar cada ano
        for ano, demandas_ano in demandas_por_ano.items():
            print(f"Processando {len(demandas_ano)} demandas do ano {ano}...")
            
            for index, demanda in enumerate(demandas_ano, 1):
                # Definir ano orçamentário
                demanda.ano_orcamentario = ano
                
                # Gerar número da demanda se não existe
                if not demanda.numero_demanda:
                    demanda.numero_demanda = f"{ano}-{index:03d}"
                
                print(f"  Demanda ID {demanda.id} -> {demanda.numero_demanda}")
        
        # Salvar alterações
        try:
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
            # Verificar resultado
            total_migradas = Demanda.query.filter(
                Demanda.ano_orcamentario.isnot(None),
                Demanda.numero_demanda.isnot(None)
            ).count()
            
            print(f"📊 Total de demandas migradas: {total_migradas}")
            
            # Mostrar estatísticas por ano
            print("\n📈 Estatísticas por ano:")
            anos = db.session.query(Demanda.ano_orcamentario).distinct().order_by(Demanda.ano_orcamentario).all()
            
            for (ano,) in anos:
                if ano:
                    count = Demanda.query.filter_by(ano_orcamentario=ano).count()
                    print(f"  {ano}: {count} demandas")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro durante a migração: {e}")
            raise

if __name__ == "__main__":
    migrar_demandas_existentes()
