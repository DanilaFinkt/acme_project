from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .forms import BirthdayForm, CongratulationForm
from .models import Birthday, Congratulation
from .utils import calculate_birthday_countdown


@login_required
def simple_view(request):
    return HttpResponse('Страница для залогиненных пользователей!')


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


# Добавляем миксин первым по списку родительских классов.
class BirthdayCreateView(LoginRequiredMixin, CreateView):
    model = Birthday
    # Не нужно описывать атрибуты: все они унаследованы от BirthdayMixin.
    form_class = BirthdayForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
    


class BirthdayUpdateView(OnlyAuthorMixin, UpdateView):
    model = Birthday
    # И здесь все атрибуты наследуются от BirthdayMixin.
    form_class = BirthdayForm

    # Определяем метод test_func() для миксина UserPassesTestMixin:
    def test_func(self):
        # Получаем текущий объект.
        object = self.get_object()
        # Метод вернёт True или False. 
        # Если пользователь - автор объекта, то тест будет пройден.
        # Если нет, то будет вызвана ошибка 403.
        return object.author == self.request.user


# Наследуем класс от встроенного ListView:
class BirthdayListView(ListView):
    # Указываем модель, с которой работает CBV...
    model = Birthday
    # ...сортировку, которая будет применена при выводе списка объектов:
    ordering = 'id'
    # ...и даже настройки пагинации:
    paginate_by = 4


class BirthdayDeleteView(OnlyAuthorMixin, DeleteView):
    model = Birthday
    success_url = reverse_lazy('birthday:list')


class BirthdayDetailView(DetailView):
    model = Birthday

    def get_context_data(self, **kwargs):
        # Получаем словарь контекста:
        context = super().get_context_data(**kwargs)
        # Добавляем в словарь новый ключ:
        context['birthday_countdown'] = calculate_birthday_countdown(
            # Дату рождения берём из объекта в словаре context:
            self.object.birthday
        )
        # Записываем в переменную form пустой объект формы.
        context['form'] = CongratulationForm()
        # Запрашиваем все поздравления для выбранного дня рождения.
        context['congratulations'] = (
            # Дополнительно подгружаем авторов комментариев,
            # чтобы избежать множества запросов к БД.
            self.object.congratulations.select_related('author')
        )
        # Возвращаем словарь контекста.
        return context


# Будут обработаны POST-запросы только от залогиненных пользователей.
@login_required
def add_comment(request, pk):
    # Получаем объект дня рождения или выбрасываем 404 ошибку.
    birthday = get_object_or_404(Birthday, pk=pk)
    # Функция должна обрабатывать только POST-запросы.
    form = CongratulationForm(request.POST)
    if form.is_valid():
        # Создаём объект поздравления, но не сохраняем его в БД.
        congratulation = form.save(commit=False)
        # В поле author передаём объект автора поздравления.
        congratulation.author = request.user
        # В поле birthday передаём объект дня рождения.
        congratulation.birthday = birthday
        # Сохраняем объект в БД.
        congratulation.save()
    # Перенаправляем пользователя назад, на страницу дня рождения.
    return redirect('birthday:detail', pk=pk)


# class CongratulationCreateView(LoginRequiredMixin, CreateView):
#     birthday = None
#     model = Congratulation
#     form_class = CongratulationForm

#     # Переопределяем dispatch()
#     def dispatch(self, request, *args, **kwargs):
#         self.birthday = get_object_or_404(Birthday, pk=kwargs['pk'])
#         return super().dispatch(request, *args, **kwargs)

#     # Переопределяем form_valid()
#     def form_valid(self, form):
#         form.instance.author = self.request.user
#         form.instance.birthday = self.birthday
#         return super().form_valid(form)

#     # Переопределяем get_success_url()
#     def get_success_url(self):
#         return reverse('birthday:detail', kwargs={'pk': self.birthday.pk})


# class BirthdayCreateView(CreateView):
#     # Указываем модель, с которой работает CBV...
#     model = Birthday
#     # Этот класс сам может создать форму на основе модели!
#     # Нет необходимости отдельно создавать форму через ModelForm.
#     # Указываем поля, которые должны быть в форме:
#     form_class = BirthdayForm
#     # Явным образом указываем шаблон:
#     template_name = 'birthday/birthday.html'
#     # Указываем namespace:name страницы, куда будет перенаправлен пользователь
#     # после создания объекта:
#     success_url = reverse_lazy('birthday:list')


# class BirthdayUpdateView(UpdateView):
#     model = Birthday
#     form_class = BirthdayForm
#     template_name = 'birthday/birthday.html'
#     success_url = reverse_lazy('birthday:list')


# def birthday(request, pk=None):
#     if pk is not None:
#         instance = get_object_or_404(Birthday, pk=pk)
#     else:
#         instance = None
#     form = BirthdayForm(
#         request.POST or None,
#         files=request.FILES or None,
#         instance=instance,
#     )
#     context = {'form': form}
#     if form.is_valid():
#         form.save()
#         birthday_countdown = calculate_birthday_countdown(
#             # ...и передаём в неё дату из словаря cleaned_data.
#             form.cleaned_data['birthday']
#         )
#         context.update({'birthday_countdown': birthday_countdown})
#     return render(request, 'birthday/birthday.html', context)


# def birthday_list(request):
#     # Получаем список всех объектов с сортировкой по id.
#     birthdays = Birthday.objects.order_by('id')
#     # Создаём объект пагинатора с количеством 10 записей на страницу.
#     paginator = Paginator(birthdays, 2)
#     # Получаем из запроса значение параметра page.
#     page_number = request.GET.get('page')
#     # Получаем запрошенную страницу пагинатора.
#     # Если параметра page нет в запросе или его значение не приводится к числу,
#     # вернётся первая страница.
#     page_obj = paginator.get_page(page_number)
#     # Вместо полного списка объектов передаём в контекст
#     # объект страницы пагинатора
#     context = {'page_obj': page_obj}
#     return render(request, 'birthday/birthday_list.html', context)


# def delete_birthday(request, pk):
#     # Получаем объект модели или выбрасываем 404 ошибку.
#     instance = get_object_or_404(Birthday, pk=pk)
#     # В форму передаём только объект модели;
#     # передавать в форму параметры запроса не нужно.
#     form = BirthdayForm(instance=instance)
#     context = {'form': form}
#     # Если был получен POST-запрос...
#     if request.method == 'POST':
#         # ...удаляем объект:
#         instance.delete()
#         # ...и переадресовываем пользователя на страницу со списком записей.
#         return redirect('birthday:list')
#     # Если был получен GET-запрос — отображаем форму.
#     return render(request, 'birthday/birthday.html', context)
