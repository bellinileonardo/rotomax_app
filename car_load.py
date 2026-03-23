from math import ceil

def organizar_carga(total_itens: int, total_paradas: int):
    # Média de itens por parada
    itens_por_parada = ceil(total_itens / total_paradas)

    paradas = []

    # Criando estrutura das paradas
    item_atual = 1
    for p in range(1, total_paradas + 1):
        itens = []
        for _ in range(itens_por_parada):
            if item_atual <= total_itens:
                itens.append(f"Item{item_atual}")
                item_atual += 1
        paradas.append({
            "parada": p,
            "itens": itens
        })

    # Definindo zonas
    def definir_zona(parada):
        if 1 <= parada <= 8:
            return "Banco Carona"
        elif 9 <= parada <= 20:
            return "Banco Traseiro"
        elif 21 <= parada <= 34:
            return "Porta-malas (Meio)"
        else:
            return "Porta-malas (Fundo)"

    # Aplicando zonas
    for p in paradas:
        p["zona"] = definir_zona(p["parada"])

    return paradas


def imprimir_plano(paradas):
    print("\n📦 PLANO DE CARGA:\n")

    for p in paradas:
        print(f"Parada {p['parada']:02d}")
        print(f"Zona: {p['zona']}")
        print(f"Itens: {', '.join(p['itens'])}")
        print("-" * 40)


if __name__ == "__main__":
    total_itens = 89
    total_paradas = 45

    plano = organizar_carga(total_itens, total_paradas)
    imprimir_plano(plano)