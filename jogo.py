import sys
import random

sys.stdout.reconfigure(encoding='utf-8')
sys.stdin.reconfigure(encoding='utf-8')

TAMANHO = 10


def rolar(n, lados):
    return sum(random.randint(1, lados) for _ in range(n))


class Heroi:
    def __init__(self, nome):
        self.nome = nome
        self.nivel = 1
        self.hp = 30
        self.hp_max = 30
        self.xp = 0
        self.xp_proximo = 100
        self.ouro = 0
        self.inventario = []
        self.ataque_base = 5

    def atacar(self):
        return rolar(1, 6) + self.nivel + self.ataque_base

    def curar(self, quantidade):
        anterior = self.hp
        self.hp = min(self.hp + quantidade, self.hp_max)
        return self.hp - anterior

    def ganhar_xp(self, xp):
        self.xp += xp
        if self.xp >= self.xp_proximo:
            self._subir_nivel()

    def _subir_nivel(self):
        self.nivel += 1
        self.xp_proximo = self.nivel * 100
        ganho = rolar(1, 6) + 2
        self.hp_max += ganho
        self.curar(ganho)
        self.ataque_base += 2
        print(f"\n★ SUBIU DE NÍVEL! {self.nome} agora é nível {self.nivel}!"
              f" +{ganho} HP máximo, +2 ataque!")

    def usar_pocao(self):
        for item in self.inventario:
            if item == "Poção de Cura":
                self.inventario.remove(item)
                cura = rolar(2, 6) + 4
                real = self.curar(cura)
                print(f"  Usou Poção de Cura! +{real} HP")
                return True
        return False

    def mostrar_ficha(self):
        blocos = int((self.hp / self.hp_max) * 20)
        barra = "█" * blocos + "░" * (20 - blocos)
        borda = "═" * (len(self.nome) + 14)
        print(f"\n╔{borda}╗")
        print(f"║  {self.nome} — Nível {self.nivel}  ║")
        print(f"║  HP:   [{barra}] {self.hp}/{self.hp_max}")
        print(f"║  XP:   {self.xp}/{self.xp_proximo}")
        print(f"║  Ouro: {self.ouro} PO")
        if self.inventario:
            print(f"║  Bag:  {', '.join(self.inventario)}")
        print(f"╚{borda}╝")


MONSTROS = [
    {"nome": "Goblin",    "hp": 10, "ataque": 3,  "xp": 15, "ouro_base": 10},
    {"nome": "Esqueleto", "hp": 15, "ataque": 4,  "xp": 25, "ouro_base": 15},
    {"nome": "Orc",       "hp": 25, "ataque": 6,  "xp": 40, "ouro_base": 25},
    {"nome": "Troll",     "hp": 50, "ataque": 10, "xp": 80, "ouro_base": 80},
]


class Monstro:
    def __init__(self, tipo=None):
        t = tipo or random.choice(MONSTROS)
        self.nome = t["nome"]
        self.hp = t["hp"]
        self.ataque_max = t["ataque"]
        self.xp = t["xp"]
        self.ouro = int(t["ouro_base"] * random.uniform(0.8, 1.2))

    def atacar(self):
        return rolar(1, self.ataque_max)

    @property
    def vivo(self):
        return self.hp > 0


def combater(heroi, monstro):
    print(f"\n⚔  COMBATE: {heroi.nome} vs {monstro.nome}! (HP {monstro.hp})")

    for rodada in range(1, 50):
        dano = heroi.atacar()
        monstro.hp -= dano
        print(f"  [{rodada}] {heroi.nome} acerta {dano} dano → "
              f"{monstro.nome}: {max(0, monstro.hp)} HP")

        if not monstro.vivo:
            heroi.ganhar_xp(monstro.xp)
            heroi.ouro += monstro.ouro
            print(f"  ☠  {monstro.nome} derrotado!"
                  f" +{monstro.xp} XP · +{monstro.ouro} PO"
                  f"  ({heroi.nome} tem {heroi.ouro} PO)")
            heroi.mostrar_ficha()
            return True

        dano_m = monstro.atacar()
        heroi.hp -= dano_m
        print(f"  [{rodada}] {monstro.nome} acerta {dano_m} dano → "
              f"{heroi.nome}: {max(0, heroi.hp)} HP")

        if heroi.hp <= 0:
            print(f"\n  {heroi.nome} foi derrotado...")
            return False

        if heroi.hp < heroi.hp_max * 0.3 and "Poção de Cura" in heroi.inventario:
            print(f"  ⚠  HP crítico! Usando poção...")
            heroi.usar_pocao()

    return True


def abrir_bau(heroi):
    print(f"\n  BAÚ ENCONTRADO!")

    ouro = rolar(2, 6) * 10
    heroi.ouro += ouro
    print(f"  Ouro: +{ouro} PO  ({heroi.nome} tem {heroi.ouro} PO)")

    cura = rolar(1, 6) + 2
    real = heroi.curar(cura)
    print(f"  Cura: +{real} HP")

    if random.random() < 0.4:
        item = random.choice(["Poção de Cura", "Elixir de Mana"])
        heroi.inventario.append(item)
        print(f"  Item encontrado: {item}!")

    heroi.mostrar_ficha()


def criar_tabuleiro():
    tab = [["." for _ in range(TAMANHO)] for _ in range(TAMANHO)]

    def colocar(simbolo, quantidade):
        colocados = 0
        while colocados < quantidade:
            r, c = random.randint(0, TAMANHO - 1), random.randint(0, TAMANHO - 1)
            if tab[r][c] == "." and (r, c) not in [(0, 0), (TAMANHO-1, TAMANHO-1)]:
                tab[r][c] = simbolo
                colocados += 1

    colocar("B", 8)
    colocar("M", 12)
    tab[TAMANHO-1][TAMANHO-1] = "E"
    return tab


def exibir_tabuleiro(tab, pos):
    print("\n  " + " ".join(str(i) for i in range(TAMANHO)))
    for r, linha in enumerate(tab):
        row = ["@" if (r, c) == pos else cel for c, cel in enumerate(linha)]
        print(f"{r} " + " ".join(row))
    print("\n  @ Herói  B Baú  M Monstro  E Saída")


def jogar():
    print("╔══════════════════════════════════╗")
    print("║      JOGO DE TABULEIRO RPG       ║")
    print("╚══════════════════════════════════╝\n")

    nome = input("Nome do herói: ").strip() or "Herói"
    heroi = Heroi(nome)
    tab = criar_tabuleiro()
    pos = (0, 0)

    heroi.mostrar_ficha()

    while True:
        exibir_tabuleiro(tab, pos)

        if heroi.hp <= 0:
            print(f"\nFIM DE JOGO — {heroi.nome} foi derrotado!")
            print(f"Ouro acumulado: {heroi.ouro} PO | XP: {heroi.xp}")
            break

        try:
            input(f"\n{heroi.nome} (HP {heroi.hp}/{heroi.hp_max} | {heroi.ouro} PO)"
                  f" — Enter para rolar o dado...")
        except (EOFError, KeyboardInterrupt):
            break

        dado = rolar(1, 6)
        print(f"Dado: {dado}")

        linha, col = pos
        col += dado
        if col >= TAMANHO:
            linha += col // TAMANHO
            col = col % TAMANHO
        linha = min(linha, TAMANHO - 1)
        pos = (linha, col)

        cel = tab[linha][col]

        if cel == "M":
            monstro = Monstro()
            if not combater(heroi, monstro):
                heroi.hp = 0
                continue
            tab[linha][col] = "."

        elif cel == "B":
            abrir_bau(heroi)
            tab[linha][col] = "."

        elif cel == "E":
            print(f"\nPARABÉNS! {heroi.nome} chegou ao destino!")
            print(f"Ouro total: {heroi.ouro} PO | XP: {heroi.xp} | Nível: {heroi.nivel}")
            heroi.mostrar_ficha()
            break


if __name__ == "__main__":
    jogar()
