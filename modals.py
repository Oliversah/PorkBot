import discord
from discord import ui
import config

palpites_registrados = {}

# Ícones atualizados para os logs de palpite
ICON_EDITADO = "https://cdn.discordapp.com/attachments/1492590020891246832/1548435564464963594/laranja1.png?ex=6aa70c7f&is=6aa5baff&hm=af5fc27071f661a61c5fb9805bb46a8e0b0feb9d81063688a49c3125a368203d&"
ICON_REGISTRADO = "https://cdn.discordapp.com/attachments/1492590020891246832/1548435692743565333/azul1.png?ex=6aa70c9d&is=6aa5bb1d&hm=cb1b24e2c861d4e264c3897e3939455bc06e37b9730991020da52ada13a503a8&"
ICON_RESULTADO = "https://cdn.discordapp.com/attachments/1492590020891246832/1541131183255982140/trophy.png?ex=6a8c79c2&is=6a8b2842&hm=18652e51e19a24a8b5c0ecccc22a945b46784d07c074ac2e2613831888c2a4b5&"


class ModalEnviarPalpite(ui.Modal, title="Enviar Palpite"):
    def __init__(self, time_casa: str, time_visitante: str, palpite_atual: tuple = None):
        super().__init__()
        self.time_casa = time_casa
        self.time_visitante = time_visitante
        self.is_edicao = palpite_atual is not None

        default_casa = palpite_atual[0] if palpite_atual else ""
        default_visitante = palpite_atual[1] if palpite_atual else ""

        self.gols_casa = ui.TextInput(
            label=f"Gols do {time_casa}",
            placeholder="0",
            default=default_casa,
            required=True,
            max_length=2
        )
        self.gols_visitante = ui.TextInput(
            label=f"Gols do {time_visitante}",
            placeholder="0",
            default=default_visitante,
            required=True,
            max_length=2
        )
        self.add_item(self.gols_casa)
        self.add_item(self.gols_visitante)

    async def on_submit(self, interaction: discord.Interaction):
        palpites_registrados[interaction.user.id] = (self.gols_casa.value, self.gols_visitante.value)

        if self.is_edicao:
            texto_autor = "Palpite Editado"
            cor_embed = discord.Color.orange()
            icon_autor = ICON_EDITADO
        else:
            texto_autor = "Palpite Registrado"
            cor_embed = discord.Color.blue()
            icon_autor = ICON_REGISTRADO

        canal_registros = interaction.guild.get_channel(config.CANAL_REGISTROS_ID)
        if canal_registros:
            descricao_log = (
                f"> **Usuário:** {interaction.user.mention} (@{interaction.user.name})\n"
                f"> **Confronto:** {self.time_casa} vs {self.time_visitante}\n"
                f"> **Palpite:** {self.time_casa} {self.gols_casa.value} x {self.gols_visitante.value} {self.time_visitante}"
            )

            embed_log = discord.Embed(
                description=descricao_log,
                color=cor_embed,
                timestamp=interaction.created_at
            )
            embed_log.set_author(name=texto_autor, icon_url=icon_autor)
            embed_log.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_log.set_footer(
                text=f"{interaction.user.display_name} (@{interaction.user.name})",
                icon_url=interaction.user.display_avatar.url
            )

            try:
                await canal_registros.send(embed=embed_log)
            except Exception as e:
                print(f"Erro ao enviar Embed para o canal de registros: {e}")

        embed_usuario = discord.Embed(
            description=(
                f"> Seu palpite: **{self.time_casa} {self.gols_casa.value} x {self.gols_visitante.value} {self.time_visitante}**\n"
                f"Caso queira alterá-lo, você poderá editar seu palpite até o início da partida."
            ),
            color=cor_embed,
            timestamp=interaction.created_at
        )
        embed_usuario.set_author(name=f"{texto_autor}!", icon_url=icon_autor)
        embed_usuario.set_thumbnail(url=interaction.user.display_avatar.url)
        embed_usuario.set_footer(text=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed_usuario, ephemeral=True)


class ModalResultadoBolao(ui.Modal, title="Encerrar Bolão"):
    def __init__(self, time_casa: str, time_visitante: str):
        super().__init__()
        self.time_casa = time_casa
        self.time_visitante = time_visitante

        self.gols_casa = ui.TextInput(
            label=f"Gols do {self.time_casa}",
            placeholder="0",
            required=True,
            max_length=2
        )
        self.gols_visitante = ui.TextInput(
            label=f"Gols do {self.time_visitante}",
            placeholder="0",
            required=True,
            max_length=2
        )
        self.add_item(self.gols_casa)
        self.add_item(self.gols_visitante)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                content="❌ Apenas administradores podem executar esta ação!",
                ephemeral=True
            )
            return

        if not self.gols_casa.value.isdigit() or not self.gols_visitante.value.isdigit():
            await interaction.response.send_message(
                content="Insira apenas números válidos no placar final!",
                ephemeral=True
            )
            return

        gols_c = self.gols_casa.value
        gols_v = self.gols_visitante.value

        vencedores = [
            f"<@{user_id}>" 
            for user_id, (p_casa, p_vis) in palpites_registrados.items() 
            if p_casa == gols_c and p_vis == gols_v
        ]

        vencedores_texto = ", ".join(vencedores) if vencedores else "Ninguém acertou o placar exato!"

        descricao = (
            f"> A partida terminou em **{self.time_casa} {gols_c} x {gols_v} {self.time_visitante}**.\n\n"
            f"**Vencedor(es):** {vencedores_texto}"
        )

        embed_resultado = discord.Embed(
            description=descricao,
            color=discord.Color.from_str("#f8a324"),
            timestamp=interaction.created_at
        )

        embed_resultado.set_author(name="Resultado do Bolão!", icon_url=ICON_RESULTADO)

        server_icon = interaction.guild.icon.url if interaction.guild.icon else None
        if server_icon:
            embed_resultado.set_thumbnail(url=server_icon)

        embed_resultado.set_footer(text=interaction.guild.name, icon_url=server_icon)

        await interaction.response.send_message(embed=embed_resultado)


class ModalTitulo(ui.Modal, title="Altere o título do seu Embed."):
    def __init__(self):
        super().__init__()
        self.titulo = ui.TextInput(label="Título", placeholder="Título do Embed", default=config.embed_builder["titulo"], required=True)
        self.titulo_url = ui.TextInput(label="URL do Título", placeholder="Ex: https://seusite.com", default=config.embed_builder["titulo_url"], required=False)
        self.add_item(self.titulo)
        self.add_item(self.titulo_url)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["titulo"] = self.titulo.value
        config.embed_builder["titulo_url"] = self.titulo_url.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalDescricao(ui.Modal, title="Altere a descrição do seu Embed"):
    def __init__(self):
        super().__init__()
        self.descricao = ui.TextInput(label="Descrição", style=discord.TextStyle.paragraph, placeholder="Digite a descrição...", default=config.embed_builder["descricao"], required=True)
        self.add_item(self.descricao)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["descricao"] = self.descricao.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalCor(ui.Modal, title="Altere a cor do seu Embed."):
    def __init__(self):
        super().__init__()
        self.cor = ui.TextInput(label="Código Hexadecimal da Cor", placeholder="Ex: #FF3B30", default=config.embed_builder["cor"], required=True)
        self.add_item(self.cor)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["cor"] = self.cor.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalAutor(ui.Modal, title="Altere o autor do seu Embed"):
    def __init__(self):
        super().__init__()
        self.autor_nome = ui.TextInput(label="Autor", placeholder="Nome do autor", default=config.embed_builder["autor_nome"], required=False)
        self.autor_icon = ui.TextInput(label="Imagem do Autor", placeholder="URL da imagem", default=config.embed_builder["autor_icon"], required=False)
        self.autor_url = ui.TextInput(label="URL do Autor", placeholder="Ex: https://seusite.com", default=config.embed_builder["autor_url"], required=False)
        self.add_item(self.autor_nome)
        self.add_item(self.autor_icon)
        self.add_item(self.autor_url)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["autor_nome"] = self.autor_nome.value
        config.embed_builder["autor_icon"] = self.autor_icon.value
        config.embed_builder["autor_url"] = self.autor_url.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalConfronto(ui.Modal, title="Configurar Confronto"):
    def __init__(self):
        super().__init__()
        self.time_casa = ui.TextInput(label="Time da Casa", placeholder="Ex: Flamengo", default=config.embed_builder["time_casa"], required=True)
        self.time_visitante = ui.TextInput(label="Time Visitante", placeholder="Ex: Palmeiras", default=config.embed_builder["time_visitante"], required=True)
        self.add_item(self.time_casa)
        self.add_item(self.time_visitante)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["time_casa"] = self.time_casa.value
        config.embed_builder["time_visitante"] = self.time_visitante.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalRodape(ui.Modal, title="Altere o rodapé do seu Embed"):
    def __init__(self):
        super().__init__()
        self.rodape_texto = ui.TextInput(label="Rodapé", placeholder="Texto do rodapé", default=config.embed_builder["rodape_texto"], required=False)
        self.rodape_icon = ui.TextInput(label="Imagem do Rodapé", placeholder="URL da imagem", default=config.embed_builder["rodape_icon"], required=False)
        self.add_item(self.rodape_texto)
        self.add_item(self.rodape_icon)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["rodape_texto"] = self.rodape_texto.value
        config.embed_builder["rodape_icon"] = self.rodape_icon.value
        from views import atualizar_painel
        await atualizar_painel(interaction)


class ModalMidia(ui.Modal, title="Altere as imagens do seu Embed"):
    def __init__(self):
        super().__init__()
        self.imagem = ui.TextInput(label="Imagem", placeholder="URL da imagem principal", default=config.embed_builder["imagem_url"], required=False)
        self.thumbnail = ui.TextInput(label="Thumbnail", placeholder="URL da thumbnail", default=config.embed_builder["thumbnail_url"], required=False)
        self.add_item(self.imagem)
        self.add_item(self.thumbnail)

    async def on_submit(self, interaction: discord.Interaction):
        config.embed_builder["imagem_url"] = self.imagem.value
        config.embed_builder["thumbnail_url"] = self.thumbnail.value
        from views import atualizar_painel
        await atualizar_painel(interaction)