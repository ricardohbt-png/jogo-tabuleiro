/* Contratos do livro do aventureiro: interface, páginas e controles sem persistência no cliente. */
const fs = require('fs');
const game = fs.readFileSync('game.js', 'utf8');
const state = fs.readFileSync('src/gameState.js', 'utf8');
const lang = fs.readFileSync('src/lang/interface.js', 'utf8');
const css = fs.readFileSync('game.css', 'utf8');
const check = (label, ok) => { console.log(`${ok ? '✅' : '❌'} ${label}`); if (!ok) process.exitCode = 1; };

console.log('[1] protocolo e acesso pelo refúgio');
check('cliente envia solicitação nativa do diário', /function openAdventurerDiary\(\)\s*\{\s*send\(\{ type: 'open_adventurer_diary' \}\)/.test(state));
check('resposta privada atualiza evento de estado', /case 'adventurer_diary_state':[\s\S]{0,100}adventurerDiaryState/.test(state));
check('livro abre a partir do painel do refúgio', game.includes("className='ref-chest-open diary-open'") && game.includes('GS.openAdventurerDiary()'));

console.log('[2] páginas e privacidade visual');
check('livro tem páginas de missões, itens e bestiário', ['missions','items','bestiary'].every(k=>game.includes(`data-diary-page="${k}"`)));
check('render bestiário lê somente registros e campos recebidos', /function _renderAdventurerDiaryPage\([\s\S]*?msg\.bestiary/.test(game));
check('páginas não entregam itens nem atualizam bestiário', !/openAdventurerDiary[\s\S]{0,400}(giveItem|grantItem|bestiary\s*\[.*\]\s*=)/.test(game));
check('fecha com Escape e restaura foco', /if\(e\.key\s*===\s*'Escape'\)/.test(game) && game.includes('_adventurerDiaryReturnFocus?.focus?.()'));
check('controles semânticos e traduções PT/EN', game.includes('role="tablist"') && lang.includes('ui.diario.titulo') && lang.includes('ui.diario.pagina_bestiario'));
check('modal responsivo', css.includes('.diario-aventureiros-overlay') && css.includes('@media'));
