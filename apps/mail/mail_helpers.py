from pybars import Compiler
 
def render_hbs_template(template_name, context):
    """
    Renders a Handlebars (HBS) template with the given context.
 
    Args:
        template_name (str): The name of the Handlebars template file located in the 'templates' directory.
        context (dict): A dictionary containing the context data to be injected into the template.
 
    Returns:
        str: The rendered HTML/string output of the compiled Handlebars template.
 
    Raises:
        Exception: If the template file is not found or rendering fails for any reason.
 
    """
    try:
        compiler = Compiler()
        hbs_file_path = f"mail/templates/{template_name}"
        with open(hbs_file_path, "r", encoding="utf-8") as f:
            source = f.read()
        template = compiler.compile(source)
        return template(context)
   
    except FileNotFoundError:
        raise Exception(f"Template {template_name} not found in templates directory")
    except Exception as e:
        raise Exception(f"Failed to render template {template_name}: {str(e)}")

