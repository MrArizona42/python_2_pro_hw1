# OpenWeatherMap Weather App

Приложение позволяет получить текущую температуру в любом крупном (и не очень) городе мира.
1. Введите токен для сервиса OpenWeatherMap. Должно появиться сообщение, что токен рабочий.

<img src="img/token_checked.png" width="320">

2. В следующем поле введите город и нажмите Enter. Должна появиться информация следующего типа:

<img src="img/city_entered.png" width="320">

3. Выберите файл с историческими данными. Файл должен содержать колонки:

`city,timestamp,temperature,season`

После загрузки файла должна появиться следующая информация:

<img src="img/raw_data.png" width="320">
<img src="img/filtered_data.png" width="320">
<img src="img/daily_temp.png" width="320">
<img src="img/roll_mean.png" width="320">
<img src="img/avg_and_outliers.png" width="320">
<img src="img/insights.png" width="320">

4. На боковой панели вы можете выбрать временной интервал, который следует учитывать для расчета статистик, и добавить другие города из введенного датасета для сравнения исторических данных

<img src="img/select_cities_and_dates.png" width="640">
