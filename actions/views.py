# from django.shortcuts import render
# from actions.utils import create_action
#
# # Create your views here.
# @login_required
# def image_create(request):
#     if request.method == 'POST':
#     # форма отправлена
#         form = ImageCreateForm(data=request.POST)
#         if form.is_valid():
# # данные в форме валидны
#             cd = form.cleaned_data
#             new_image = form.save(commit=False)
# # назначить текущего пользователя элементу
#             new_image.user = request.user
#             new_image.save()
#             create_action(request.user, 'bookmarked image', new_image)
#             messages.success(request, 'Image added successfully')
# # перенаправить к представлению детальной
# # информации о только что созданном элементе
#             return redirect(new_image.get_absolute_url())
#         else:
# # скомпоновать форму с данными,
# # предоставленными букмарклетом методом GET
#             form = ImageCreateForm(data=request.GET)
#             return render(request,
#     'images/image/create.html',
#     {'section': 'images',
# 'form': form})