from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (CommandHandler, Filters, MessageHandler, Updater ,ConversationHandler)
from pymongo import MongoClient
import logging 
import datetime

from conf.settings import BASE_API_URL, TELEGRAM_TOKEN,CONECTION_MONGO


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

client = MongoClient(CONECTION_MONGO)
db = client.banco1
users = db.user

novoValor = ''
novotipo=''
VALUE,DEBIT,CREDIT = range(3)
dt = datetime.datetime.today()

def start(bot, update):
    response_message = ' MyBudget  \n' \
     'O bot para te ajudar no controle das finanças pessoais:  \n' \
     ' Tenha controle em tempo real sobre suas despesas  \n' \
     'Centralize todas suas compras e tenha controle das suas despesas:  \n' \
     'Veja a lista de comandos abaixo:  \n' \
     '  \n' \
     '/saldo - valor disponivel para o mes \n ' \
     '/resumo - diagnotico do mes  \n' \
     '/estatistica - seu relatório em 3 meses  \n' \
     '/minhameta - informações da meta  \n' \
     '/novacompra - inserir nova compra   \n' \

    update.message.reply_text(response_message)

def help(bot, update):
    response_message = 'Veja a lista de comandos abaixo:  \n' \
     '  \n' \
     '/saldo - valor disponivel para o mes \n ' \
     '/resumo - diagnotico do mes  \n' \
     '/estatistica - seu relatório  \n' \
     '/minhameta - informações da meta  \n' \
     '/novacompra - inserir nova compra   \n' \
    
    update.message.reply_text(response_message)

def infoMes(user):
    documents = users.find_one({'Nome' : user.first_name})
    compras = documents['Compras']
    mes = compras[str(dt.month)+'/'+str(dt.year)]
    valueInCard = float(mes['Cartao']) 
    valueInDebit = float(mes['Debito'])
    meta = float(documents['Meta'])
    gasto = valueInCard + valueInDebit
    saldo = meta - gasto
    percent = gasto / meta * 100

    return  meta,saldo,gasto,valueInCard,valueInDebit, percent

def saldo(bot, update):
    meta,saldo,gasto,valueInCard,valueInDebit, percent = infoMes( update.message.from_user)
    response_message = 'Saldo disponível: R$'+ str(saldo)+  ' \n'
    update.message.reply_text(response_message)
    bot.sendPhoto(
        chat_id=update.message.chat_id,
        photo=BASE_API_URL + "{type:'horizontalBar',data:{labels:['"+ str(dt.month)+'/'+str(dt.year) +"'], datasets:[{label:'Saldo',data:["+ str(saldo)+ "]},{label:'Meta',data:["+ str(meta)+ "]}]},options: {scales: {xAxes: [{ticks: {beginAtZero: true}}]}}}"
    )
    if(gasto > meta):
        bot.send_message(
        chat_id=update.message.chat_id,
        text='Você infelizmente já perdeu a meta '
        )
    else:
        bot.send_message(
        chat_id=update.message.chat_id,
        text='Parabéns!! Você se encontra dentro da meta. '
        )
    
def resumo(bot, update):
     meta,saldo,gasto,valueInCard,valueInDebit, percent = infoMes( update.message.from_user)
     response_message = 'Seus Resumo Mensal \n' 
     response_message += 'Meta R$: ' + str(meta)  + '\n'
     response_message += 'Saldo Disponível R$: ' + str(saldo) + '\n'
     response_message += 'Gasto do Mês R$: ' + str(gasto) + '\n'
     response_message += 'Gasto no Debito R$: ' + str(valueInDebit) + '\n'
     response_message += 'Gasto no Cartão de Crédito R$: ' + str(valueInCard) + '\n'
    
     update.message.reply_text(response_message)
     bot.send_message(
        chat_id=update.message.chat_id,
        text='Percentual Gasto do Mês'
     )
     bot.sendPhoto(
        chat_id=update.message.chat_id,
        photo=BASE_API_URL + '{type:%27radialGauge%27,data:{datasets:[{data:['+str(percent) +'],backgroundColor:%27green%27}]}}'
     )

def minhameta(bot, update):
    user = update.message.from_user
    documents = users.find_one({'Nome' : user.first_name})
    response_message = 'Sua meta mensal é: R$ '
    response_message += documents['Meta']
    update.message.reply_text(response_message)

def infoEstat(user,mes,ano):
    documents = users.find_one({'Nome' : user.first_name})
    compras = documents['Compras']
    mes = compras[str(mes)+'/'+str(ano)]
    valueInCard = float(mes['Cartao']) 
    valueInDebit = float(mes['Debito'])
    gasto = valueInCard + valueInDebit
    meta = float(documents['Meta'])
    saldo = meta - gasto

    return  saldo,gasto
    
def estatistica(bot, update):
    response_message = ' Seus últimos 3 meses  \n' 
    update.message.reply_text(response_message)
    saldoMes1,gastoMes1  =  infoEstat(update.message.from_user,dt.month - 2,dt.year)
    saldoMes2,gastoMes2  =  infoEstat(update.message.from_user,dt.month - 1,dt.year)
    saldoMes3,gastoMes3  =  infoEstat(update.message.from_user,dt.month ,dt.year)
    bot.sendPhoto(
        chat_id=update.message.chat_id,
        photo=BASE_API_URL + "{type:'bar',data:{labels:['"+ str(dt.month - 2)+'/'+str(dt.year) +"','"+ str(dt.month - 1)+'/'+str(dt.year) +"','"+ str(dt.month)+'/'+str(dt.year) +"'], datasets:[{label:'Gasto',data:["+str(gastoMes1)+","+str(gastoMes2)+","+str(gastoMes3)+"]}]}}"  
    )
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Total Gasto R$'  + str (int(gastoMes1 + gastoMes2 + gastoMes3))
     )
    bot.send_message(
        chat_id=update.message.chat_id,
        text='Total Economizado R$'  + str(int(saldoMes1 + saldoMes2 + saldoMes3))
     )

def novacompra(bot, update):
    reply_keyboard = [['Débito', 'Crédito']]
    response_message = ' Qual a forma de pagamento \n'
    update.message.reply_text(response_message,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return VALUE

def valor( bot,update ):
    text = update.message.text
    response_message = ' Insira um valor, nesse formato: 000.00  \n'
    update.message.reply_text(response_message)
    if text == 'Débito':
        return DEBIT
    if text == 'Crédito':
        return CREDIT

def debito(bot , update):
    user = update.message.from_user
    documents = users.find_one({'Nome' : user.first_name})
    compras = documents['Compras']
    mes = compras[str(dt.month)+'/'+str(dt.year)]
    text = update.message.text
    logger.info("Debit %s",  text)
    valueDebit = float(mes['Debito']) + float(text)
    valueCard = float(mes['Cartao']) 
    compras[str(dt.month)+'/'+str(dt.year)] = {
        'Cartao': str(valueCard),
        'Debito': str(valueDebit)
    }
    result = users.find_one_and_update(
    {'_id' : documents['_id']}, {"$set":
            {'Compras' : compras} 
        }
    )
    response_message = ' Valor Insido com sucesso!  \n'
    update.message.reply_text(response_message)
    return ConversationHandler.END

def credito(bot , update):
    user = update.message.from_user
    documents = users.find_one({'Nome' : user.first_name})
    compras = documents['Compras']
    mes = compras[str(dt.month)+'/'+str(dt.year)]
    text = update.message.text
    logger.info("Credit %s",  text)
    valueDebit = float(mes['Debito']) 
    valueCard = float(mes['Cartao']) + float(text)
    compras[str(dt.month)+'/'+str(dt.year)] = {
        'Cartao': str(valueCard),
        'Debito': str(valueDebit)
    }
    result = users.find_one_and_update(
    {'_id' : documents['_id']}, {"$set":
            {'Compras' : compras} 
        }
    )
    response_message = ' Valor Insido com sucesso!  \n'
    update.message.reply_text(response_message)
    return ConversationHandler.END

def unknown(bot, update):
    response_message = "Insira um comando"
    update.message.reply_text(response_message)

def cancel(update, context):
    update.message.reply_text('Operação Cancelada')
    return ConversationHandler.END

def main():
    updater = Updater(token=TELEGRAM_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('saldo', saldo))
    dispatcher.add_handler(CommandHandler('resumo', resumo))
    dispatcher.add_handler(CommandHandler('minhaMeta', minhameta))
    dispatcher.add_handler(CommandHandler('estatistica', estatistica))
    # dispatcher.add_handler(MessageHandler(Filters.command, unknown))


    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('novacompra', novacompra)],

        states={
            VALUE: [MessageHandler(Filters.text , valor)],

            DEBIT: [MessageHandler(Filters.text , debito)],

            CREDIT: [MessageHandler(Filters.text , credito)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)


    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    print("press CTRL + C to cancel.")
    main()
