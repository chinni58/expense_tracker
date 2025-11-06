from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth
from .models import Expense
from .forms import ExpenseForm
from datetime import date, timedelta

def index(request):
    expenses = Expense.objects.order_by('-date', '-created_at')[:200]
    today_total = Expense.objects.filter(date=date.today()).aggregate(total=Sum('amount'))['total'] or 0
    this_month_total = Expense.objects.filter(date__year=date.today().year, date__month=date.today().month)\
                                      .aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'expenses/index.html', {
        'expenses': expenses,
        'today_total': today_total,
        'this_month_total': this_month_total,
    })

def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('expenses:index')
    else:
        form = ExpenseForm(initial={'date': date.today()})
    return render(request, 'expenses/expense_form.html', {'form': form, 'title':'Add Expense'})

def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('expenses:index')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title':'Edit Expense'})

def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        return redirect('expenses:index')
    return render(request, 'expenses/confirm_delete.html', {'expense': expense})

def daily_report(request):
    # Get all expenses from the last 30 days
    start_date = date.today() - timedelta(days=30)
    expenses = Expense.objects.filter(date__gte=start_date).order_by('-date')

    # Group by date manually (safe way without TruncDate)
    daily_totals = {}
    for exp in expenses:
        daily_totals.setdefault(exp.date, 0)
        daily_totals[exp.date] += exp.amount

    # Convert to list of tuples sorted by newest first
    daily_data = sorted(daily_totals.items(), key=lambda x: x[0], reverse=True)

    # Today's total (separately for quick display)
    today_total = daily_totals.get(date.today(), 0)

    context = {
        'daily_data': daily_data,
        'today_total': today_total,
    }
    return render(request, 'expenses/daily_report.html', context)

def monthly_report(request):
    # Total per month
    qs = Expense.objects.annotate(month=TruncMonth('date')) \
                        .values('month') \
                        .annotate(total=Sum('amount')) \
                        .order_by('-month')
    monthly = list(qs)
    # current month total
    this_month = date.today().replace(day=1)
    monthly_total = Expense.objects.filter(date__year=this_month.year, date__month=this_month.month) \
                                   .aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'expenses/monthly_report.html', {'monthly': monthly, 'monthly_total': monthly_total})
