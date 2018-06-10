# coding: utf8
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils import timezone
from exchange.settings import logger
from order_book.models import Order, Transaction, Transaction3
from order_book.order_service import close_buy_order, close_sell_order
from .models import news, historyBuy, shapePrice
from Users.models import USER_COMPANY, USER_BROKER, USER_ADMIN, USER_MANAGER, User, Company
from Users.forms import OpenCompanyForm
import datetime, decimal
from django.core.exceptions import MultipleObjectsReturned
from controlpanel.models import Tiket, Message, FAQS
from controlpanel.forms import AddTiketForm
import time, random
from django.db.models import Q
from django.views.decorators.clickjacking import xframe_options_exempt


def cab_common(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                com.user = request.user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        return render(request, 'mainpage.html' if local else 'externpage.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

@login_required
def cab(request):
    return cab_common(request, request.user, local=True)

@xframe_options_exempt
def cab_ext(request, user_name):
    if True:
        user = User.objects.get(username=user_name)
        return cab_common(request, user, local=False)
    #except:
    #    raise Http404


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def history(request):
    # historyList = historyBuy.objects.filter(user=request.user)
    # total = 0
    # for i in historyList:
    #     total += i.price
    total = 0
    hist = Order.objects.filter(is_active=False, amount__gt=0, user=request.user).order_by('-id')
    for i in hist:
        total += i.price

    return render(request, 'historyView.html', {'historyList': hist, 'total': total})

def checkPendingOrders(pk):
    company = Company.objects.get(pk=pk)

    for data in Order.objects.filter(Q(company_id=pk), Q(order_type="BUY"), ~Q(status='canceled'), ~Q(status='completed')):
        buyuser = User.objects.get(pk=data.user_id)
        if data.price == int(company.currentSharePrice):
            buyuser.balance -= (data.price - data.stop_loss) * data.amount
            company.user.balance += (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount -= data.amount
            company.totalSharesSold += data.amount
            data.status = 'bought'
            buyuser.save()
            company.user.save()
            data.save()
        if data.stop_loss >= company.currentSharePrice:
            buyuser.balance -= (data.price - data.stop_loss) * data.amount
            company.user.balance += (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount -= data.amount
            company.totalSharesSold += data.amount
            data.status = 'completed'
            data.closed_at = timezone.now()
            data.is_active = False

            HB = historyBuy(
                    user=buyuser,
                    count=data.amount,
                    company=company,
                    price=data.amount * data.price,
                    stop_loss=data.stop_loss,
                    take_profit=data.take_profit
                )
            buyuser.save()
            company.user.save()
            data.save()
            HB.save()
        if data.take_profit <= company.currentSharePrice:
            buyuser.balance += (data.price - data.stop_loss) * data.amount
            company.user.balance -= (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount -= data.amount
            company.totalSharesSold += data.amount
            data.status = 'completed'
            data.closed_at = timezone.now()
            data.is_active = False

            HB = historyBuy(
                    user=buyuser,
                    count=data.amount,
                    company=company,
                    price=data.amount * data.price,
                    stop_loss=data.stop_loss,
                    take_profit=data.take_profit
                )
            buyuser.save()
            company.user.save()
            data.save()
            HB.save()

def buyAndSaleProcess(company_id):
    company = Company.objects.get(pk=company_id)

    # check buy orders
    for data in Order.objects.filter(company_id=company_id, order_type="BUY", is_active=True):
        buyuser = User.objects.get(pk=data.user_id)
        if data.stop_loss <= company.sharePrice:
            buyuser.balance -= (data.price - data.stop_loss) * data.amount
            company.user.balance += (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount -= data.amount
            company.totalSharesSold += data.amount
            data.closed_at = timezone.now()
            data.is_active = False
            buyuser.save()
            company.user.save()
            data.save()
        if data.take_profit >= company.sharePrice:
            buyuser.balance += (data.price - data.stop_loss) * data.amount
            company.user.balance -= (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount -= data.amount
            company.totalSharesSold += data.amount
            data.closed_at = timezone.now()
            data.is_active = False
            buyuser.save()
            company.user.save()
            data.save()

    # check sell orders
    for data in Order.objects.filter(company_id=company_id, order_type="SELL", is_active=True):
        buyuser = User.objects.get(pk=data.user_id)
        if data.stop_loss <= company.sharePrice:
            buyuser.balance += (data.price - data.stop_loss) * data.amount
            company.user.balance -= (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount += data.amount
            company.totalSharesSold -= data.amount
            data.closed_at = timezone.now()
            data.is_active = False
            buyuser.save()
            company.user.save()
            data.save()
        if data.take_profit >= company.sharePrice:
            buyuser.balance -= (data.price - data.stop_loss) * data.amount
            company.user.balance += (data.price - data.stop_loss) * data.amount
            company.availableSharesAmount += data.amount
            company.totalSharesSold -= data.amount
            data.closed_at = timezone.now()
            data.is_active = False
            buyuser.save()
            company.user.save()
            data.save()

# @user_passes_test(lambda u: u.rightUser == USER_BROKER, login_url='Users:login')
def buyShares(request):
    if request.method == "POST":
        try:
            company = Company.objects.get(pk=int(request.POST['company']))
            amount = int(request.POST['sharesAmount'])
            price = int(request.POST['sharePrice'])

            try:
                stop_loss = int(request.POST['stopLoss'])
            except:
                stop_loss = None
            try:
                take_profit = int(request.POST['takeProfit'])
            except:
                take_profit = None


            # return error if stop loss higher than or equal to company's price
            if stop_loss != None:
                if int(company.sharePrice) < stop_loss or int(company.sharePrice) == stop_loss:
                    return JsonResponse({'error':'Stop loss value can\'t be higher than or equal to Company\'s share price'})

            # return error if take profit lower than or equal to company's price
            if take_profit != None:
                if int(company.sharePrice) > take_profit or int(company.sharePrice) == take_profit:
                    # return JsonResponse({'error':"Take profit value can't be lower than or equal to Company's share price"})
                    pass



            # return false if company has lower available shares amount as user enters
            if company.availableSharesAmount < amount:
                # return JsonResponse({'error':"Company hasn't got {} share amount".format(amount)})
                pass


            sp = shapePrice(
                company=company,
                price=company.currentSharePrice,
                priceTrans=company.sharePrice
            )
            sp.save()

            # create BUY order if user share price is not equal to company share price
            if int(company.currentSharePrice) != price:

                # if amount > 0 and price > 0 and stop_loss > 0 and take_profit > 0 and company:
                #     if stop_loss < price < take_profit:
                order = Order(user=request.user, company=company, order_type='BUY',
                      amount=amount, price=price, stop_loss=stop_loss,
                      take_profit=take_profit)
                order.save()
                return JsonResponse({'done':"Done"})
                # Transaction3(buyer=request.user, seller=company, amount=amount, order=order, price=price).save()
            else:
                if request.user.balance < amount * company.currentSharePrice:
                    return JsonResponse({'error':"You have insufficient money to buy shares"})
                else:
                    request.user.balance -= amount * company.currentSharePrice
                    company.user.balance += amount * company.currentSharePrice
                    request.user.save()
                    company.user.save()
                    # decrease available shares amount and increase total shares amount
                    company.availableSharesAmount -= amount
                    company.totalSharesSold += amount

                    order = Order(user=request.user, company=company, order_type='BUY',
                          amount=amount, price=price, stop_loss=stop_loss,
                          take_profit=take_profit, status='bought')
                    order.save()
                    return JsonResponse({'done':"Done"})

                    # increase company's current share price
                    # formula = (0.5*amount)/100 * company.currentSharePrice
                    company.sharePrice = company.currentSharePrice
                    company.currentSharePrice += decimal.Decimal((0.5*amount)/100) * company.currentSharePrice
                    # company.totalSharesSold += int(request.POST['sharePrice'])

                    company.save()
                    HB = historyBuy(
                            user=request.user,
                            count=int(request.POST['sharePrice']),
                            company=company,
                            price=int(request.POST['sharePrice']) * company.currentSharePrice,
                            stop_loss=int(request.POST['stopLoss']) * company.currentSharePrice,
                            take_profit=int(request.POST['takeProfit']) * company.currentSharePrice
                        )
                    request.user.save()

            checkPendingOrders(int(request.POST['company']))

            # return HttpResponseRedirect(reverse('cab:index'))
            return redirect(request.META.get('HTTP_REFERER'))
        except Exception as e:
            print(e)
            print(e)
            print(e)

        except User.DoesNotExist:
            raise
        except ValueError:
            raise
        return HttpResponse(status=500)
    else:
        return HttpResponse(status=405)


# @user_passes_test(lambda u: u.rightUser == USER_BROKER, login_url='Users:login')
def sellShare(request):
    if request.method == "POST":
        try:
            order = Order.objects.get(pk=int(request.POST['company']))
            company = order.company
            # company = Company.objects.get(pk=int(request.POST['company']))
            amount = int(request.POST['sharesAmount'])

            availableAmount = order.amount

            if amount > availableAmount:
                return JsonResponse({'error':"You dont have that much"})

            # return false if company has lower available shares amount as user enters
            if company.availableSharesAmount < amount:
                return JsonResponse({'error':"Company hasn't got {} share amount".format(amount)})

            sp = shapePrice(
                company=company,
                price=company.currentSharePrice,
                priceTrans=company.sharePrice
            )
            sp.save()
            if int(company.sharePrice) == order.price:
                if amount == availableAmount:
                    request.user.balance += amount * company.currentSharePrice
                    company.user.balance -= amount * company.currentSharePrice
                    request.user.save()
                    company.user.save()
                    # decrease available shares amount and increase total shares amount
                    company.availableSharesAmount += amount
                    company.totalSharesSold -= amount

                    # increase company's current share price
                    # formula = (0.5*amount)/100 * company.currentSharePrice
                    company.sharePrice = company.currentSharePrice
                    company.currentSharePrice -= decimal.Decimal((0.5*amount)/100) * company.currentSharePrice
                    # company.totalSharesSold += int(request.POST['sharePrice'])
                    order.status = 'completed'
                    order.is_active = False
                    order.closed_at = timezone.now()
                    order.save()
                    company.save()
                else:
                    request.user.balance += amount * company.currentSharePrice
                    company.user.balance -= amount * company.currentSharePrice
                    request.user.save()
                    company.user.save()
                    # decrease available shares amount and increase total shares amount
                    company.availableSharesAmount += amount
                    company.totalSharesSold -= amount

                    # increase company's current share price
                    # formula = (0.5*amount)/100 * company.currentSharePrice
                    company.sharePrice = company.currentSharePrice
                    company.currentSharePrice -= decimal.Decimal((0.5*amount)/100) * company.currentSharePrice
                    # company.totalSharesSold += int(request.POST['sharePrice'])
                    order.amount -= amount
                    order.save()
                    company.save()

            else:
                if company.user.balance < amount * company.currentSharePrice:
                    return JsonResponse({'error':"You can't sell shares this time"})
                else:
                    request.user.balance += amount * company.currentSharePrice
                    company.user.balance -= amount * company.currentSharePrice
                    request.user.save()
                    company.user.save()
                    # decrease available shares amount and increase total shares amount
                    company.availableSharesAmount += amount
                    company.totalSharesSold -= amount

                    # increase company's current share price
                    # formula = (0.5*amount)/100 * company.currentSharePrice
                    company.sharePrice = company.currentSharePrice
                    company.currentSharePrice -= decimal.Decimal((0.5*amount)/100) * company.currentSharePrice
                    # company.totalSharesSold += int(request.POST['sharePrice'])

                    company.save()

                    request.user.save()

                    # get company
            checkPendingOrders(company.id)

        except User.DoesNotExist:
            pass
        except ValueError:
            pass
        return HttpResponseRedirect(reverse('cab:index'))
    else:
        return HttpResponse(status=405)

# @user_passes_test(lambda u: u.rightUser == USER_BROKER, login_url='Users:login')
def sellShares(request):
    if request.method == "POST":
        try:

            company = Company.objects.get(pk=int(request.POST['company']))
            amount = int(request.POST['sharesAmount'])
            price = int(request.POST['sharePrice'])
            stop_loss = int(request.POST['stopLoss'])
            take_profit = int(request.POST['takeProfit'])

            if int(company.currentSharePrice) < stop_loss or int(company.sharePrice) == stop_loss:
                return JsonResponse({'error':'Stop loss value can\'t be higher than or equal to Company\'s share price'})

            # return error if take profit lower than or equal to company's price
            if int(company.currentSharePrice) > take_profit or int(company.sharePrice) == take_profit:
                return JsonResponse({'error':"Take profit value can't be lower than or equal to Company's share price"})

            # if user share price is equal to company's price, make transaction, else order it
            if int(company.sharePrice) == price:
                pass

            # return false if company has lower available shares amount as user enters
            if company.availableSharesAmount < amount:
                return JsonResponse({'error':"Company hasn't got {} share amount".format(amount)})
            # count = 0
            # for i in historyBuy.objects.filter(user=request.user, company=company):
            #     if i.price > 0:
            #         count += i.count
            #     elif i.price < 0:
            #         count -= i.count
            # if count >= int(request.POST['sharePrice']):
            #     request.user.balance += int(request.POST['sharePrice']) * company.currentSharePrice
            #     company.user.balance -= int(request.POST['sharePrice']) * company.currentSharePrice
            #     company.user.save()
            #     HB = historyBuy(
            #         user=request.user,
            #         count=int(request.POST['sharePrice']),
            #         company=company,
            #         price=-int(request.POST['sharePrice']) * company.currentSharePrice
            #     )
            #     request.user.save()
            #     company.sharePrice = company.currentSharePrice
            #     company.currentSharePrice -= int(company.currentSharePrice * decimal.Decimal(0.10))
            #     # company.currentSharePrice -= int(request.POST['sharePrice']) * company.currentSharePrice * decimal.Decimal(0.10)
            #     # company.oldSharePrice = company.sharePrice + company.sharePrice * decimal.Decimal(0.01)
            #     company.totalSharesSold -= int(request.POST['sharePrice'])
            #     company.save()
            #     sp = shapePrice(
            #         company=company,
            #         price=company.currentSharePrice,
            #         priceTrans=company.sharePrice
            #     )
            #     sp.save()
            #     HB.save()

            company.sharePrice = company.currentSharePrice
            company.currentSharePrice -= int(company.currentSharePrice * decimal.Decimal(0.10))
            company.totalSharesSold -= int(request.POST['sharePrice'])
            company.save()
            sp = shapePrice(
                company=company,
                price=company.currentSharePrice,
                priceTrans=company.sharePrice
            )
            sp.save()
            logger.info(company)
            if int(company.sharePrice) == price:
                if amount > 0 and price > 0 and stop_loss > 0 and take_profit > 0 and company:
                    if stop_loss < price < take_profit:
                        Order(user=request.user, company=company, order_type='SELL',
                              amount=amount, price=price, stop_loss=stop_loss,
                              take_profit=take_profit).save()
                        # close_sell_order(order=order)
            else:
                if company.user.balance < amount * company.currentSharePrice:
                    return JsonResponse({'error':"You can't sell shares this time"})
                else:
                    request.user.balance += amount * company.currentSharePrice
                    company.user.balance -= amount * company.currentSharePrice
                    request.user.save()
                    company.user.save()
                    # decrease available shares amount and increase total shares amount
                    company.availableSharesAmount += amount
                    company.totalSharesSold -= amount

                    # increase company's current share price
                    # formula = (0.5*amount)/100 * company.currentSharePrice
                    company.sharePrice = company.currentSharePrice
                    company.currentSharePrice -= decimal.Decimal((0.5*amount)/100) * company.currentSharePrice
                    # company.totalSharesSold += int(request.POST['sharePrice'])

                    company.save()
                    HB = historyBuy(
                            user=request.user,
                            count=int(request.POST['sharePrice']),
                            company=company,
                            price=int(request.POST['sharePrice']) * company.currentSharePrice,
                            stop_loss=int(request.POST['stopLoss']) * company.currentSharePrice,
                            take_profit=int(request.POST['takeProfit']) * company.currentSharePrice
                        )
                    request.user.save()

                    # get company
                    buyAndSaleProcess(int(request.POST['company']))

        except User.DoesNotExist:
            pass
        except ValueError:
            pass
        return HttpResponseRedirect(reverse('cab:index'))
    else:
        return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def dataChart(request):
    if request.method == "POST":
        try:
            if request.POST['flag'] == 'true':
                company = Company.objects.get(pk=int(request.POST['pk']))
                SP = shapePrice.objects.filter(company=company)
                try:
                    max, min = 0, SP[0].price
                except IndexError:
                    max = 0
                    min = 0
                data = []
                for i in SP:
                    data.append(i.price)
                    max = i.price if i.price > max else max
                    min = i.price if i.price < min else min

                return JsonResponse({
                    'result': 'success',
                    'count': SP.count(),
                    'max': max,
                    'min': min,
                    'name': company.name,
                    'datas': data
                })
            else:
                return JsonResponse({'price': Company.objects.get(pk=int(request.POST['pk'])).currentSharePrice})
        except User.DoesNotExist:
            return JsonResponse({'result': 'error'})
        except ValueError:
            return JsonResponse({'result': 'error'})
    return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def dataNews(request):
    if request.method == "POST":
        # try:
        datas = [[i.date.strftime("%Y-%m-%d %H:%M:%S"), i.head] for i in
                 news.objects.filter(pk=int(request.POST['pk']))]
        return JsonResponse({'result': 'success', 'news': datas})
        # except news.DoesNotExist:
        #    return JsonResponse({'result': 'error'})
        # except ValueError:
        #    return JsonResponse({'result': 'error'})
    return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def dataInformations(request):
    if request.method == "POST":
        try:
            inf = Company.objects.get(pk=int(request.POST['pk']))
            result = {
                'name': inf.name, 'CSP': inf.currentSharePrice, 'TSA': inf.availableSharesAmount + inf.totalSharesSold,
                'TSS': inf.totalSharesSold, 'TSV': inf.sharePrice * inf.availableSharesAmount,
                'PWBS': historyBuy.objects.filter(company=inf).count(),
                'SH': inf.sharePrice,
                'CSPM': round(decimal.Decimal(100) - inf.sharePrice / inf.currentSharePrice * 100, 2), 'ASA': inf.availableSharesAmount,
            }
            return JsonResponse({'result': 'success', 'inf': result})
        except Company.DoesNotExist:
            pass
        except ValueError:
            pass
    return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def FAQ(request):
    return render(request, 'FAQ.html', {'Tikets': FAQS.objects.filter(public=True)})


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def openTiket(request, pk):
    f = None
    try:
        f = FAQS.objects.get(pk=int(pk))
    except FAQS.DoesNotExist:
        raise Http404
    return render(request, 'editTiketCab.html', {'t': f})


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def editTiket(request, pk):
    t = None
    try:
        t = Tiket.objects.get(pk=int(pk))
    except Tiket.DoesNotExist:
        return Http404
    if request.method == "GET":
        return render(request, 'editTiketCab.html', {"Tiket": t,
                                                     'mess': Message.objects.filter(tiket=t),
                                                     'form': AddTiketForm()
                                                     })
    elif request.method == "POST":
        form = AddTiketForm(request.POST)
        if form.is_valid():
            mess = form.save(commit=False)
            mess.user = request.user
            mess.tiket = Tiket.objects.get(pk=int(pk))
            mess.save()
            t.count += 1
            t.date_last_edit = mess.date
            t.save()
            return HttpResponseRedirect(reverse('cab:FAQ'))
        return render(request, 'editTiketCab.html', {"Tiket": t,
                                                     'mess': Message.objects.filter(tiket=t),
                                                     'form': form
                                                     })
    else:
        return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def dataCompanyPrice(request):
    if request.method == "POST":
        data = [[i.id, i.currentSharePrice] for i in Company.objects.all()]
        return JsonResponse({'result': 'success', 'data': data})
    else:
        return HttpResponse(status=405)


@user_passes_test(lambda u: u.rightUser == USER_BROKER or u.rightUser == USER_COMPANY, login_url='Users:login')
def dataChartTwo(request):
    if request.method == "POST":
        com = Company.objects.get(pk=int(request.POST['pk']))
        # if random.randint(0,1) == 0:
        data = [
            [
                i.date.strftime("%Y:%m:%d:%H:%M:%S"),
                round(i.price, 2),
                round(i.priceTrans, 2) if i.priceTrans > i.price else round(i.price, 2),
                round(i.priceTrans, 2) if i.priceTrans < i.price else round(i.price, 2),
                round(i.priceTrans, 2)
            ] for i in shapePrice.objects.filter(company=com)]
        # else:
        #    data = [[i.date.strftime("%Y:%m:%d:%H:%M:%S"),round(i.price, 2), round(i.price+i.price*decimal.Decimal(0.01), 2),
        #    round(i.price+i.price*decimal.Decimal(0.01), 2), round(i.price, 2)] for i in shapePrice.objects.filter(company=com)]
        return JsonResponse({'result': 'success', 'data': data, 'company': com.name})
    else:
        return HttpResponse(status=405)


@login_required
def resetPassword(request):
    if request.method == "POST":
        mess = ''
        if request.user.check_password(request.POST['oldPass']):
            if request.POST['pass'] == request.POST['pass2']:
                if len(request.POST['pass']) > 8:
                    request.user.set_password(request.POST['pass'])
                    request.user.save()
                    mess = "Password reset success!"
                else:
                    mess = "Length of the password is less than 8 symbols"
            else:
                mess = "Passwords don't coincide"
        else:
            mess = "The old password doesn't coincide"
        return render(request, 'resetPasswordCab.html', {'mess': mess})
    else:
        return render(request, 'resetPasswordCab.html')


@login_required
def lastShapePrice(request):
    if request.method == "POST":
        try:
            com = Company.objects.get(pk=int(request.POST['pk']))
            result = shapePrice.objects.filter(company=com).order_by('date')[0]
            data = [
                round(result.price, 2),
                round(result.priceTrans, 2) if result.priceTrans > result.price else round(result.price, 2),
                round(result.priceTrans, 2) if result.priceTrans < result.price else round(result.price, 2),
                round(result.priceTrans, 2)
            ]
            return JsonResponse({'result': 'success', 'data': data})
        except:
            return JsonResponse({'result': 'error'})
    return HttpResponse(status=405)












def cab_common2(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                com.user = request.user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        user_company_id = Company.objects.filter(user=user).first()
        return render(request, 'mainpage2.html' if local else 'externpage2.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 'user_company_id':user_company_id.id,
                                                 'user_company_name':user_company_id.name,
                                                 'user':user,
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

# @login_required
# def cab2(request):
#     return cab_common2(request, request.user, local=True)

# @login_required
def cab2(request,username):
    # print(username)
    try:
        user = User.objects.filter(username=username).get()
    except:
        return HttpResponse("Not A Valid User")

    return cab_common2(request, user, local=True)













def cab_common3(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                # com.user = request.user
                com.user = user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        user_company_id = Company.objects.filter(user=user).first()
        return render(request, 'mainpage3.html' if local else 'externpage2.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 'user_company_id':user_company_id.id,
                                                 'user':user,
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

# @login_required
def cab3(request,username):

    try:
        user = User.objects.filter(username=username).get()
    except:
        return HttpResponse("Not A Valid User")


    return cab_common3(request, user, local=True)
    # return cab_common3(request, request.user, local=True)








def cab_common4(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                com.user = user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        user_company_id = Company.objects.filter(user=user).first()
        
        return render(request, 'mainpage4.html' if local else 'externpage2.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 'user_company_id':user_company_id.id,
                                                 'user':user,
                                                 
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

# @login_required
def cab4(request,username):

    try:
        user = User.objects.filter(username=username).get()
    except:
        return HttpResponse("Not A Valid User")

    return cab_common4(request, user, local=True)









def cab_common5(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                com.user = user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        user_company_id = Company.objects.filter(user=user).first()
        user_company = Company.objects.filter(user=user).first()
        return render(request, 'mainpage5.html' if local else 'externpage2.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 'user_company_id':user_company_id.id,
                                                 'user':user,
                                                 'user_company':user_company,
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

# @login_required
def cab5(request,username):

    try:
        user = User.objects.filter(username=username).get()
    except:
        return HttpResponse("Not A Valid User")

    return cab_common5(request, user, local=True)








def cab_common6(request, user, local):
    if user.rightUser != USER_ADMIN and user.rightUser != USER_MANAGER:
        if request.method == "POST":
            form = OpenCompanyForm(request.POST)
            if form.is_valid():
                com = form.save(commit=False)
                com.user = user
                com.currentSharePrice = com.sharePrice + com.sharePrice * decimal.Decimal(0.01)
                com.save()
                return HttpResponseRedirect(reverse('cab:index'))
        else:
            form = OpenCompanyForm()
        n = news.objects.filter(public=True)
        company = Company.objects.select_related().all()
        history = historyBuy.objects.select_related().filter(date__range=(
            datetime.datetime.now().replace(hour=0, minute=0, second=0),
            datetime.datetime.now().replace(hour=23, minute=59, second=59)
        ))
        UserComp = False
        try:
            c = Company.objects.get(user=user)
        except Company.DoesNotExist:
            UserComp = True
        except MultipleObjectsReturned:
            c = Company.objects.filter(user=user)[0]

        # GET CURRENT ACTIVE TRANSACTIONS
        orders = Order.objects.filter(is_active=True, user=user, status="bought")
        result_orders = []
        for o in orders:
            if o.user == user:
                result_orders.insert(0, o)
            else:
                result_orders.append(o)
        # get pending orders of user
        pending_orders = Order.objects.filter(status='pending', user=user, is_active=True)
        # for order in pending_orders:
        #     seller = order.company


        # GET PENDING TRANSACTIONS
        pending_transactions = Transaction.objects.filter(status='pending')
        pending = []
        transactions = []
        for transaction in pending_transactions:
            # try to finish transaction
            # if stop loss and take profit checked
            # else add to result transactions list
            b_order = transaction.buy_order
            s_order = transaction.sell_order
            buyer = b_order.user
            seller = s_order.user

            s_new_amount = 0
            b_new_amount = 0
            # count total amount and total price
            if b_order.amount < s_order.amount:
                total_amount = b_order.amount
                price = b_order.price
                s_new_amount = s_order.amount - b_order.amount
            else:
                total_amount = s_order.amount
                price = s_order.price
                b_new_amount = b_order.amount - s_order.amount
            transaction.total_amount = total_amount
            transaction.save()
            # total prices
            b_total_price = b_order.price * total_amount
            s_total_price = s_order.price * total_amount
            total_price = total_amount * price

            # profits
            b_profit_value = b_total_price - total_price
            s_profit_value = s_total_price - total_price
            logger.err(b_order.company.sharePrice)
            logger.err(b_order.price)
            logger.err(total_amount)
            b_pr = (b_order.company.sharePrice - b_order.price) * total_amount
            s_pr = (s_order.company.sharePrice - s_order.price) * total_amount
            b_profit_value += b_pr
            s_profit_value += s_pr
            # company current price


            # check buyer balance here
            if buyer.balance > total_price:
                # Stop Loss and Take profit here
                logger.ok(
                    'B_O TP: %s, PROFIT: %s, B_O SL:%s' % (b_order.take_profit, b_profit_value, abs(b_order.stop_loss)))
                if b_order.take_profit <= b_profit_value < abs(b_order.stop_loss):
                    if s_order.take_profit <= s_profit_value < abs(s_order.stop_loss):
                        # complete transaction
                        seller.balance += total_price
                        buyer.balance -= total_price
                        buyer.save()
                        seller.save()

                        b_order.is_active = False
                        b_order.amount -= total_amount
                        b_order.closed_at = timezone.now()

                        s_order.is_active = False
                        s_order.amount -= total_amount
                        s_order.closed_at = timezone.now()
                        b_order.save()
                        s_order.save()
                        # create order with new amount
                        if s_new_amount:
                            Order(order_type='SELL', user=seller, company=s_order.company, amount=s_new_amount, price=s_order.price,
                                  stop_loss=s_order.stop_loss, take_profit=s_order.take_profit).save()
                        if b_new_amount:
                            Order(order_type='BUY', user=buyer, company=b_order.company, amount=b_new_amount, price=b_order.price,
                                  stop_loss=b_order.stop_loss, take_profit=b_order.take_profit).save()
                        transaction.status = 'completed'
                        transaction.b_profit = b_profit_value
                        transaction.s_profit = s_profit_value
                        transaction.save()

            if transaction.buy_order.user == user:
                pending.insert(0, transaction.buy_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.buy_order)
                transactions.append(transaction.id)
            if transaction.sell_order.user == user:
                pending.insert(0, transaction.sell_order)
                transactions.insert(0, transaction.id)
            else:
                pending.append(transaction.sell_order)
                transactions.append(transaction.id)
        user_company_id = Company.objects.filter(user=user).first()
        return render(request, 'mainpage6.html' if local else 'externpage2.html', {'news': n,
                                                 'orders': result_orders,
                                                 'company': company,
                                                 'pending': pending,
                                                 'pending_orders':pending_orders,
                                                 'transactions': transactions,
                                                 'history': history,
                                                 'UserComp': UserComp,
                                                 'OpenCompanyForm': form,
                                                 'defaultCompany': company[0],
                                                 'pk': c.id,
                                                 'user_company_id':user_company_id.id,
                                                 'user':user,
                                                 })
    return HttpResponseRedirect(reverse('controlpanel:managenews'))

# @login_required
def cab6(request,username):

    try:
        user = User.objects.filter(username=username).get()
    except:
        return HttpResponse("Not A Valid User")

    return cab_common6(request, user, local=True)
