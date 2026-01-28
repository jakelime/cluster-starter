# Django Guidebook

## Guide - Core

- django3.2 tutorial playlist

  - [Tutorial by CodingEntrepreneurs](https://youtube.com/watch?v=SlHBNXW1rTk&list=PLEsfXFp6DpzRMby_cSoWTFw8zaMdTEXgL)
  - [Tutorial by CodingEntrepreneurs (updated)](https://www.youtube.com/watch?v=I_IchaIdmnA)
    - For this project, we choose not to use Tailwind but stick to Bootstrap5 for various reasons (I think.).
    - The usage of HTMX is more refined here, do follow his guides here.

- Key objectives

  - MVT
    - models (data structure)
    - urls (routers)
    - views (logic)
    - templates (frontend ui)
  - Other concepts for ease-of-development
    - `forms.py`
      - automatically populate forms using `crispy` (taking reference from models)
    - `apptables.py`
      - automatically render tables, pagination (taking reference from models)
    - `appfilters.py`
      - automatically render tables, pagination (taking reference from models)

- Self-Implemented Project best-practices
  - Use Class-Based views **AS MUCH AS POSSIBLE**
    - CreateView, DetailView, UpdateView, DeleteView
    - For more advanced needs, go lower level to use `TemplateView` or even `View`
    - Go even higher level to use `SingleTableView`, `SingleTableMixin` for table views.
    - Use `FilterView` for filter views
      - FilterView uses `django-filters` which implements filtering from the backend, not front-end
      - It might not suit your needs, but remember to manage yourself - critical requirements vs. complexities
  - In models, use `get_*_urls(self)`
    - `get_absolute_url`, `get_change_url`, `get_add_url`, get_delete_url`
    - These methods will also help you write custom functions to show in tables easily.
  - In Django, permissions are automatically created: `view`, `add`, `change` and `delete`
    - Let's stick to the default naming for ease of development
    - e.g. in views, `permission_required = ["engines.view_leadingordermodel"]`
  - In Templates, folder structure is designed for our use-case
    - Most modules/app shares the same layout: Dashboard style
    - Use `partials/*.html` for HTMX reactive loadings
    - Use `commons/*.html` so that we don't have so many duplicated `create.html`, `update.html`, etc.
