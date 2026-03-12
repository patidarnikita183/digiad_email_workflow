from typing import Dict, List, Any, Tuple
import datetime
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.platypus import Indenter
from reportlab.lib.units import inch
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

#local imports
from pdf_generation.pdf_utils import generate_fle_name

class FlexiblePDFGenerator:
    def __init__(self, filename="output.pdf", pagesize=A4, footer_text=None):
        """
        Initialize PDF generator
        
        Args:
            filename: Output PDF filename
            pagesize: Page size (A4, letter, etc.)
            footer_text: Custom footer text (if None, will show date)
        """
        self.filename = filename
        self.pagesize = pagesize
        self.footer_text = footer_text
        
        # SOLUTION 1: Increase bottom margin to reserve space for footer
        footer_height = 0.3 * inch  # Reserve more space for footer
        
        self.doc = SimpleDocTemplate(filename, 
                                   pagesize=pagesize,
                                   leftMargin=0.5*inch,
                                   rightMargin=0.5*inch,
                                   topMargin=0.2*inch,
                                   bottomMargin=footer_height)  # Increased from 0.3 to 0.5
        
        self.story = []
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles with proper hierarchy"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )

        # Platform heading - larger and more prominent
        self.platform_heading_style = ParagraphStyle(
            'PlatformHeading',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=5,
            spaceBefore=10,
            textColor=colors.black,
            fontName='Times-Bold'
        )

        # Table and plot headings - smaller than platform heading
        self.section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=8,
            textColor=colors.HexColor('#374151'),  # Dark gray
            fontName='Times-Bold'
        )
        
        # Table description style - new addition
        self.table_description_style = ParagraphStyle(
            'TableDescription',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            spaceBefore=0,
            textColor=colors.HexColor("#4D525A"),  # Medium gray
            fontName='Times-Roman',
            alignment=0,  # Left alignment
            leading=14
        )
        
        # Keep the old subtitle style for backward compatibility
        self.subtitle_style = self.section_heading_style

    def _add_footer(self, canvas, doc):
        """
        Add footer to each page with proper positioning
        
        Args:
            canvas: ReportLab canvas object
            doc: Document object
        """
        canvas.saveState()
        
        # Set font for footer
        canvas.setFont('Times-Roman', 9)
        
        # Get page dimensions
        width, height = self.pagesize
        
        canvas.setFillColor(colors.HexColor("#4D525A")) 
        
        # SOLUTION 2: Position footer within the reserved bottom margin space
        # Use the same bottom margin value as defined in __init__
        footer_y_position = 0.25*inch  # Position footer within the 0.5" bottom margin
        
        # Add page number on the right
        page_num = canvas.getPageNumber()
        canvas.drawRightString(width - 0.5*inch, footer_y_position, f"Page {page_num}")
        
        # Add custom footer text on the left if provided
        # if self.footer_text:
        canvas.drawString(0.5*inch, footer_y_position, "www.digiad.ai")
        
        canvas.restoreState()

    def set_footer_text(self, text: str):
        """Set custom footer text"""
        self.footer_text = text
   
    def add_title(self, title_text: str):
        """Add main title to PDF"""
        title = Paragraph(title_text, self.title_style)
        self.story.append(title)
        self.story.append(Spacer(1, 12))

    def add_navigation_section(self, platforms_list: List[str]):
        """
        Create navigation buttons with compact widths and balanced spacing.
        """
        self.story.append(Paragraph("✧ Platform Analytics", self.section_heading_style))
        self.add_table_description("Click on a platform to navigate its analytics section:", space_after=False)
        self.story.append(Spacer(1, -12))
        button_style = ParagraphStyle(
            'NavigationButton',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=1,  # Center text
        )

        button_row = []
        col_widths = []
        spacing = 8  # fixed space between buttons (you can tweak this)

        for idx, platform in enumerate(platforms_list):
            anchor = f"#{platform.lower().replace(' ', '_')}_section"

            button_para = Paragraph(
                f'<link href="{anchor}" color="white">{platform}</link>',
                button_style
            )

            button_table = Table([[button_para]], rowHeights=[28])  # auto width per button
            button_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#4F6FFF')),
                ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor("#CACACA")),
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
                ('ROUNDEDCORNERS', (0, 0), (0, 0), 6),
                ('LEFTPADDING', (0, 0), (0, 0), 6),
                ('RIGHTPADDING', (0, 0), (0, 0), 6),
                ('TOPPADDING', (0, 0), (0, 0), 4),
                ('BOTTOMPADDING', (0, 0), (0, 0), 4),
            ]))

            # Add button
            button_row.append(button_table)
            col_widths.append(button_table.wrap(0, 0)[0])

            # Add spacer column (except after last button)
            if idx < len(platforms_list) - 1:
                button_row.append(Spacer(spacing, 1))
                col_widths.append(spacing)

        # Wrap row into a container table
        container_table = Table([button_row], hAlign='LEFT', colWidths=col_widths, spaceBefore=10)
        container_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        # Add indentation by wrapping with a left margin Spacer
        self.story.append(Spacer(1, 0))  # vertical space (optional)
        self.story.append(Indenter(left=30, right=0))  # 30 units indentation
        self.story.append(container_table)
        self.story.append(Indenter(left=-30, right=0))  # reset indentation

    def add_platform_heading(self, heading_text: str, platform_name: str = None):
            """Add platform heading with navigation anchor"""
            # Create anchor for navigation
            if platform_name:
                anchor_name = platform_name.lower().replace(" ", "_") + "_section"
                heading_with_anchor = f'<a name="{anchor_name}"/>{heading_text}'
            else:
                heading_with_anchor = heading_text
                
            heading = Paragraph(heading_with_anchor, self.platform_heading_style)
            self.story.append(heading)
            # self.story.append(Spacer(1, 5))
        
    def add_section_heading(self, heading_text: str):
        """Add section heading for tables/plots (smaller than platform heading)"""
        heading = Paragraph(heading_text, self.section_heading_style)
        self.story.append(heading)
        # self.story.append(Spacer(1, 3))
    
    def add_table_description(self, description_text: str,space_after: int = True):
        """Add descriptive text for table data"""
        description = Paragraph(description_text, self.table_description_style)
        self.story.append(description)
        if space_after:
            self.story.append(Spacer(1, 3))
    
    def add_text(self, text: str, style_name: str = 'Normal', title: str = None):
        """
        Add text content to PDF
        
        Args:
            text: Text content to add
            style_name: Style to use ('Normal', 'Heading1', 'Heading2', etc.)
            title: Optional section title
        """
        if title:
            title_para = Paragraph(title, self.section_heading_style)
            self.story.append(title_para)
        
        text_para = Paragraph(text, self.styles[style_name])
        self.story.append(text_para)
        self.story.append(Spacer(1, 12))
    
    def generate_table_description(self, df: pd.DataFrame, title: str = None) -> str:
        """
        Generate a concise, user-friendly description for the table data.
        
        Args:
            df: pandas DataFrame
            title: Table title for context
            
        Returns:
            str: Generated description
        """
        if df.empty:
            return "This table does not contain any data for the selected period."
        
        num_rows = len(df)
        columns_lower = [col.lower() for col in df.columns]
        
        # Detect top+bottom rows format (separator row with '...')
        has_separator = any(
            (row.astype(str) == "...").all() for _, row in df.iterrows()
        )
        if any('age' in col for col in columns_lower) and any('gender' in col for col in columns_lower):
            return (
                "This table shows the top-five and bottom-five age–gender combinations based on advertising performance."
                if has_separator else
                "This table provides advertising performance metrics segmented jointly by age groups and gender."
            )
                # Age demographics
        elif any('language' in col for col in columns_lower):
            return (
                "This table shows the top-five and bottom-five language segments based on advertising performance."
                if has_separator else
                "This table provides advertising performance based on different language segments."
            )
        
        # Age demographics
        elif any('age' == col for col in columns_lower):
            return (
                "This table shows the top-five and bottom-five age groups based on advertising performance."
                if has_separator else
                "This table provides advertising performance based on different age groups."
            )
        
        # Gender demographics
        elif any('gender' in col for col in columns_lower):
            return (
                "This table shows the top-five and bottom-five gender segments in terms of campaign performance."
                if has_separator else
                "This table shows how advertising performance varies across male, female, and other gender categories."
            )
        # Time-slot based
        elif any(word in col for col in columns_lower for word in ['time_slot']):
            return (
                "This table shows the top-five and bottom-five performing time slots for the campaign."
                if has_separator else
                "This table shows campaign performance segmented by different time slots."
            )

        # Time-based data
        elif any(word in col for col in columns_lower for word in ['hour','date', 'day', 'week', 'month']):
            return (
                "This table shows the top-five and bottom-five performing time periods for the campaign."
                if has_separator else
                f"This table summarizes campaign performance trends across {num_rows} time periods."
            )
        
        elif any(word in col for col in columns_lower for word in ['device_platform']):
            return (
                "This table ranks the top-five and bottom-five device-platform types by campaign performance."
                if has_separator else
                "This table shows how advertising performance differs across device-platform categories."
            )
        
        # Device breakdown
        elif any(word in col for col in columns_lower for word in ['device']):
            return (
                "This table ranks the top-five and bottom-five device types by campaign performance."
                if has_separator else
                "This table shows how advertising performance differs across device categories."
            )
        
        # Platform breakdown
        elif any(word in col for col in columns_lower for word in ['platform']):
            return (
                "This table identifies the top-five and bottom-five platforms by campaign performance."
                if has_separator else
                "This table presents campaign performance metrics across different platforms."
            )
        
        # Placement performance
        elif any(word in col for col in columns_lower for word in ['display_name', 'placement']):
            return (
                "This table highlights the top-five and bottom-five ad placements based on campaign performance."
                if has_separator else
                "This table provides campaign performance insights across different ad placements."
            )
        
        # Interest categories
        elif any(word in col for col in columns_lower for word in ['interest', 'interest_category_name']):
            return (
                "This table shows the top-five and bottom-five interest categories by audience engagement."
                if has_separator else
                "This table presents performance metrics segmented by different audience interest categories."
            )
        # Location-based
        elif any(word in col for col in columns_lower for word in ['location', 'country', 'region', 'city']):
            return (
                "This table shows the top-five and bottom-five geographic regions based on advertising performance."
                if has_separator else
                "This table provides campaign performance metrics across locations."
            )
        
        # Operating systems
        elif any(word in col for col in columns_lower for word in ['operating_system', 'os']):
            return (
                "This table shows the top-five and bottom-five operating systems ranked by advertising performance."
                if has_separator else
                "This table shows campaign performance segmented by different operating systems."
            )
        
        # General fallback
        else:
            return (
                "This table shows the top-five and bottom-five records from the dataset."
                if has_separator else
                f"This table provides an overview of campaign performance across {num_rows} records."
                )
    
    def add_matplotlib_figure(self, fig, title: str = None, 
                            width: float = None, height: float = None,
                            dpi: int = 500):
        """
        Add matplotlib figure to PDF with proper sizing
        """
        if title:
            self.add_section_heading(title)
        
        # Use sensible default sizing for single charts
        if width is None and height is None:
            # Make single charts a good readable size
            width = 4*inch  # Reasonable size for single charts
            height = 2.8*inch  # Good aspect ratio
        elif width is None:
            width = height * 1.4  # Maintain aspect ratio
        elif height is None:
            height = width * 0.7  # Maintain aspect ratio
        
        # Save figure to bytes buffer
        img_buffer = io.BytesIO()
        fig.savefig(img_buffer, format='PNG', dpi=dpi, bbox_inches='tight')
        img_buffer.seek(0)
        
        # Create image from buffer
        chart_image = Image(img_buffer, width=width, height=height)
        self.story.append(chart_image)
        self.story.append(Spacer(1, 10))
               
    def add_horizontal_line(self, width="100%", thickness=0.5, color=colors.HexColor("#3A3D41"), 
                        spaceBefore=8, spaceAfter=10):
        """
        Add a horizontal line separator
        
        Args:
            width: Line width ("100%" for full page width or specific value)
            thickness: Line thickness in points
            color: Line color
            spaceBefore: Space before line
            spaceAfter: Space after line
        """
        self.story.append(Spacer(1, spaceBefore))
        
        hr = HRFlowable(width=width, thickness=thickness, 
                    color=color, spaceBefore=0, spaceAfter=0)
        self.story.append(hr)
        
        # self.story.append(Spacer(1, spaceAfter))

    def add_page_break(self):
        """Add a page break"""
        self.story.append(PageBreak())
    
    def add_spacer(self, height: int = 12):
        """Add vertical space"""
        self.story.append(Spacer(1, height))
    
    def generate_pdf(self):
        """Generate the final PDF file"""
        try:
            self.doc.build(self.story, 
                            onFirstPage=self._add_footer, 
                            onLaterPages=self._add_footer)
            # self.doc.build(self.story)
            print(f"PDF generated successfully: {self.filename}")
            return self.filename
        except Exception as e:
            print(f"Error generating PDF: {e}")
            raise

    def add_gradient_bar(self, height=0.3*inch, start_color='#1E40AF', end_color='#06B6D4'):
        """
        Add a gradient bar stretched full page width.
        """
        page_width, _ = A4  # Full width in points

        # Create drawing with full page width
        drawing = Drawing(page_width, height)

        # Create gradient effect
        num_segments = 100
        segment_width = page_width / num_segments

        for i in range(num_segments):
            ratio = i / (num_segments - 1)

            # Parse hex
            start_r = int(start_color[1:3], 16) / 255.0
            start_g = int(start_color[3:5], 16) / 255.0
            start_b = int(start_color[5:7], 16) / 255.0

            end_r = int(end_color[1:3], 16) / 255.0
            end_g = int(end_color[3:5], 16) / 255.0
            end_b = int(end_color[5:7], 16) / 255.0

            # Interpolate
            r = start_r + (end_r - start_r) * ratio
            g = start_g + (end_g - start_g) * ratio
            b = start_b + (end_b - start_b) * ratio

            rect = Rect(i * segment_width, 0, segment_width, height)
            rect.fillColor = colors.Color(r, g, b)
            rect.strokeColor = None
            drawing.add(rect)

        # Get the available width from the document template
        available_width = self.doc.width
        
        # Scale the drawing to fit the available width and extend to margins
        drawing.width = available_width
        drawing.renderScale = available_width / page_width
        drawing.hAlign = "LEFT"
        
        self.story.append(drawing)

    def prepare_dataframe_for_display(self, df: pd.DataFrame, max_rows: int = None, 
                                    show_top_and_bottom: bool = True) -> Tuple[pd.DataFrame, str]:
        """
        Prepare dataframe for display by showing top and bottom performers when appropriate
        
        Args:
            df: pandas DataFrame to prepare
            max_rows: Maximum rows to display (if None, show all)
            show_top_and_bottom: Whether to show both top and bottom segments
            
        Returns:
            Tuple of (prepared_dataframe, note_text)
        """
        if df.empty:
            return df, ""
        
        # Always add row index column (1-based numbering)
        df_with_index = df.copy()
        df_with_index.insert(0, 'S No.', range(1, len(df_with_index) + 1))
        
        if max_rows is None:
            return df_with_index

        # If show_top_and_bottom is False, just return head
        if not show_top_and_bottom:
            return df_with_index.head(max_rows)
        
        total_rows = len(df_with_index)
        
        # If dataframe has fewer rows than max_rows, show all
        if total_rows <= max_rows:
            return df_with_index
        else:
            # For larger max_rows, show equal split between top and bottom
            top_count = max_rows // 2
            bottom_count = max_rows - top_count

        
        # Get top and bottom segments with original row indices preserved
        top_df = df_with_index.head(top_count).copy()
        bottom_df = df_with_index.tail(bottom_count).copy()
        
        # Create separator row to indicate the gap
        if len(df_with_index.columns) > 0:
            separator_data = ['...'] * len(df_with_index.columns)
            separator_df = pd.DataFrame([separator_data], columns=df_with_index.columns)
            
            # Combine top, separator, and bottom
            display_df = pd.concat([top_df, separator_df, bottom_df], ignore_index=True)
        else:
            display_df = pd.concat([top_df, bottom_df], ignore_index=True)
                
        return display_df

    def add_dataframe(self, display_df, title: str = None, max_rows: int = None,
                        description: str = None, show_top_and_bottom: bool = False):
        """
        Add a pandas DataFrame to the PDF as a table with optional title, description,
        row limits, and top+bottom display.
        """
        try:
            # Ensure display_df is a proper DataFrame
            if not isinstance(display_df, pd.DataFrame):
                self.add_table_description("Invalid data format provided.")
                return
                
            if display_df.empty:
                self.add_table_description("No data available for display.")
                return

            # Prepare DataFrame (this will add S No. column and handle truncation)
            display_df= self.prepare_dataframe_for_display(display_df, max_rows, show_top_and_bottom)


            # Convert to table data with better error handling
            headers = [str(h) for h in display_df.columns.tolist()]
            
            # Get raw data and handle potential issues
            try:
                raw_rows = display_df.values.tolist()
            except Exception as e:
                self.add_table_description(f"Error processing dataframe data: {str(e)}")
                return

            col_count = len(headers)
            
            # Improved data conversion with error handling
            data_rows = []
            for row_idx, row in enumerate(raw_rows):
                converted_row = []
                for col_idx in range(col_count):
                    try:
                        if col_idx >= len(row):
                            converted_row.append("0")
                        elif pd.isna(row[col_idx]):
                            converted_row.append("0")
                        else:
                            converted_row.append(str(row[col_idx]))
                    except Exception as e:
                        print(f"Warning: Error converting cell [{row_idx}, {col_idx}]: {e}")
                        converted_row.append("")
                data_rows.append(converted_row)

            if not headers or not data_rows:
                self.add_table_description("No valid data to display.")
                return

            table_data = [headers] + data_rows
            table = Table(table_data, repeatRows=1)

            # Enhanced styling with special formatting for S No. column and separator rows
            style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduced from 12
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, 0), 4),  # Reduced padding
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                
                # Set data rows to white background
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1F2937')),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),  # Reduced from 10
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),  # Apply to all cells
                ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                
                ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ]
            
            # Special styling for S No. column (first column)
            style.extend([
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),  # Light gray for S No. column
                ('FONTNAME', (0, 1), (0, -1), 'Times-Bold'),  # Bold for row numbers
                ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#495057')),  # Dark gray text
            ])
            
            # Special styling for separator rows (rows with '...')
            for row_idx, row_data in enumerate(data_rows):
                if any(str(cell) == '...' for cell in row_data):
                    style.extend([
                        ('BACKGROUND', (0, row_idx + 1), (-1, row_idx + 1), colors.HexColor('#F3F4F6')),
                        ('TEXTCOLOR', (0, row_idx + 1), (-1, row_idx + 1), colors.HexColor('#9CA3AF')),
                        ('FONTNAME', (0, row_idx + 1), (-1, row_idx + 1), 'Helvetica-Oblique'),
                        ('ALIGN', (0, row_idx + 1), (-1, row_idx + 1), 'CENTER'),
                    ])

            table.setStyle(TableStyle(style))

            # Add title if given
            if title:
                # self.story.append(Paragraph(f"<b>{title}</b>", self.styles['Heading3']))
                self.add_section_heading(title)
                self.story.append(Spacer(1, 6))

            if description is None:
                description = self.generate_table_description(display_df, title=title)
            
            if description:
                self.add_table_description(description)

            # Align table to the left with indentation
            table.hAlign = 'LEFT'   # Left align
            table.spaceBefore = 0
            table.spaceAfter = 12

            # Wrap in outer table to add indentation
            indented_table = Table([[table]])
            indented_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 30),  # Adjust 30 for indentation
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))

            self.story.append(indented_table)
            self.story.append(Spacer(1, 12))

        except Exception as e:
            print(f"Error in add_dataframe: {str(e)}")
            # self.add_table_description(f"Error displaying DataFrame: {str(e)}")

    def _create_compact_table(self, display_df):
        """
        Helper method to create a compact table with error handling and row indices
        """
        try:
            if display_df.empty:
                return None
            
            # Prepare DataFrame (this will add S No. column if not present)
            if 'S No.' not in display_df.columns:
                display_df = self.prepare_dataframe_for_display(display_df, max_rows=None, show_top_and_bottom=False)
                
            # Convert DataFrame to table data with proper error handling
            headers = [str(h) for h in display_df.columns.tolist()]
            
            # Get raw data safely
            try:
                raw_rows = display_df.values.tolist()
            except Exception as e:
                print(f"Error getting table data: {e}")
                return None
            
            # Convert data safely
            table_data_rows = []
            for row_idx, row in enumerate(raw_rows):
                converted_row = []
                for col_idx in range(len(headers)):
                    try:
                        if col_idx >= len(row):
                            converted_row.append("0")
                        elif pd.isna(row[col_idx]):
                            converted_row.append("0")
                        else:
                            converted_row.append(str(row[col_idx]))
                    except Exception as e:
                        print(f"Warning: Error converting cell [{row_idx}, {col_idx}]: {e}")
                        converted_row.append("")
                table_data_rows.append(converted_row)
            
            table_data = [headers] + table_data_rows
            table = Table(table_data, hAlign="LEFT")
            
            # Compact table style with enhanced S No. column styling
            compact_table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reduced from 12
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, 0), 4),  # Reduced padding
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                
                # Set data rows to white background
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1F2937')),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),  # Reduced from 10
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),  # Apply to all cells
                ('RIGHTPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                
                ('GRID', (0, 1), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ]
            
            # Special styling for S No. column (first column)
            compact_table_style.extend([
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),  # Light gray for S No. column
                ('FONTNAME', (0, 1), (0, -1), 'Times-Bold'),  # Bold for row numbers
                ('TEXTCOLOR', (0, 1), (0, -1), colors.HexColor('#495057')),  # Dark gray text
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Center align row numbers
            ])
            
            # Special styling for separator rows
            for row_idx, row_data in enumerate(table_data_rows):
                if any(str(cell) == '...' for cell in row_data):
                    compact_table_style.extend([
                        ('BACKGROUND', (0, row_idx + 1), (-1, row_idx + 1), colors.HexColor('#F3F4F6')),
                        ('TEXTCOLOR', (0, row_idx + 1), (-1, row_idx + 1), colors.HexColor('#9CA3AF')),
                        ('FONTNAME', (0, row_idx + 1), (-1, row_idx + 1), 'Helvetica-Oblique'),
                        ('ALIGN', (0, row_idx + 1), (-1, row_idx + 1), 'CENTER'),
                    ])
            
            # Apply styling to table
            table.setStyle(TableStyle(compact_table_style))
            return table
            
        except Exception as e:
            print(f"Error creating compact table: {e}")
            return None

    def add_two_tables_and_side_by_side_graphs(self, df1, df2, fig1, fig2, 
                                        table1_title=None, table2_title=None,
                                        fig1_title=None, fig2_title=None,
                                        table1_description=None, table2_description=None,
                                        max_rows=None, show_top_and_bottom=True):
        """
        Add two tables (one below another) followed by two graphs side by side on same page
        """
        
        try:
            # Prepare dataframes for display (this will add S No. columns)
            display_df1 = self.prepare_dataframe_for_display(df1, max_rows, show_top_and_bottom)
            display_df2 = self.prepare_dataframe_for_display(df2, max_rows, show_top_and_bottom)
            
            # Add first table with smaller spacing
            if table1_title:
                self.add_section_heading(table1_title)
            
            # Add description for first table
            if table1_description is None:
                table1_description = self.generate_table_description(display_df1, table1_title)
            if table1_description:
                self.add_table_description(table1_description)
            
            # Create first table with error handling
            table1 = self._create_compact_table(display_df1)
            if table1:
                self._add_indented_table(table1)
                            
            self.story.append(Spacer(1, 10))  # Reduced spacing
            
            # Add second table
            if table2_title:
                self.add_section_heading(table2_title)
            
            # Add description for second table
            if table2_description is None:
                table2_description = self.generate_table_description(display_df2, table2_title)
            if table2_description:
                self.add_table_description(table2_description)
            
            # Create second table with error handling
            table2 = self._create_compact_table(display_df2)
            if table2:
                self._add_indented_table(table2)
            
            self.story.append(Spacer(1, 10))  # Space before graphs
            
            # Create side-by-side graphs
            if fig1 and fig2:
                self.add_side_by_side_graphs(fig1, fig2, fig1_title, fig2_title)
                
        except Exception as e:
            print(f"Error in add_two_tables_and_side_by_side_graphs: {str(e)}")
            self.add_table_description(f"Error displaying tables and graphs: {str(e)}")

    def _add_indented_table(self, table):
        """
        Helper method to add an indented table
        """
        try:
            indent = 0.4 * inch
            indented_table_data = [[Spacer(indent, 0), table]]
            container = Table(indented_table_data, colWidths=[indent, None])
            container.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            self.story.append(container)
            
        except Exception as e:
            print(f"Error adding indented table: {e}")
            self.add_table_description(f"Error displaying table: {str(e)}")

    def add_side_by_side_graphs(self, fig1, fig2, title1=None, title2=None):
        """
        Add two matplotlib figures side by side
        
        Args:
            fig1, fig2: matplotlib figure objects
            title1, title2: Optional titles for the graphs
        """
        # Save figures to bytes buffers with smaller size and lower DPI for compactness
        fig1.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.95)
        fig2.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.95)
        
        img_buffer1 = io.BytesIO()
        fig1.savefig(img_buffer1, format='PNG', dpi=250, bbox_inches='tight')
        img_buffer1.seek(0)
        
        img_buffer2 = io.BytesIO()
        fig2.savefig(img_buffer2, format='PNG', dpi=250, bbox_inches='tight')
        img_buffer2.seek(0)
        
        # Calculate available width for side-by-side layout
        available_width = self.doc.width
        graph_width = available_width * 0.48  # Use 48% of available width for each graph
        graph_height = graph_width * 0.6  # Maintain reasonable aspect ratio
        
        # Create images with calculated dimensions
        chart1 = Image(img_buffer1, width=graph_width, height=graph_height)
        chart2 = Image(img_buffer2, width=graph_width, height=graph_height)
        
        # Create table to hold images side by side
        if title1 and title2:
            # If titles provided, include them in the table
            title_style = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=0,
            spaceBefore=0,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#374151'),  # Dark gray
            fontName='Times-Bold'
        )
            
            graph_data = [
                [chart1, chart2],
                [Spacer(1, 5), Spacer(1, 5)],  # Small spacer between title and graph
                [Paragraph(title1, title_style), Paragraph(title2, title_style)]
            ]
        else:
            graph_data = [[chart1, chart2]]
        
        self.story.append(Spacer(1, 10))  # Space before graphs
        # Create table for side-by-side layout
        graph_table = Table(graph_data, colWidths=[graph_width, graph_width], hAlign="LEFT")
        graph_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        self.story.append(graph_table)
    
    def add_campaign_first_page(self, campaign_info: Dict[str, Any], campaign_data: Dict[str, Any] = None,platforms_list=None, report_title: str = "Campaign Performance Report"):
        """
        Add a professional first page with campaign details in letter format
        Args:
        campaign_info (dict): Dictionary containing:
            - campaign_name: Name of the campaign
            - customer_name: Customer company name
            - brand_name: Brand name
            - logo_path: Path to DigiAd logo (optional)
            - platforms: List of advertising platforms
            - start_date: Campaign start date
            - end_date: Campaign end date
        campaign_data (dict): Dictionary containing platform data and insights            
        """        
        
        # Style for the main body text
        body_style = ParagraphStyle(
            'BodyText',
            parent=self.styles['Normal'],
            fontSize=12,
            fontName='Times-Roman',
            textColor=colors.black,
            spaceAfter=12,
            alignment=4,  # Justified alignment
            leading=16,   # Line spacing
            leftIndent=0,
            rightIndent=0
        )
        # Style for campaign details box
        detail_box_style = ParagraphStyle(
            'DetailBox',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Times-Roman',
            textColor=colors.black,
            spaceAfter=6,
            alignment=0,  # Left alignment
            leading=14,
            leftIndent=20,
            rightIndent=20,
            borderWidth=1,
            borderColor=colors.HexColor('#E5E7EB'),
            borderPadding=12,
            backColor=colors.HexColor('#F9FAFB')
        )
            
        # Style for section headers
        section_header_style = ParagraphStyle(
            'PlatformHeading',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=5,
            spaceBefore=10,
            textColor=colors.black,
            fontName='Times-Bold'
        ) 
        
        # Style for insights and actions content
        insight_style = ParagraphStyle(
            'InsightStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Times-Roman',
            textColor=colors.black,
            spaceAfter=4,
            alignment=0,  # Left alignment
            leading=13,
            leftIndent=16,
            bulletIndent=10
        )

        # Add DigiAd logo if provided
        if campaign_info.get('logo_path') and os.path.exists(campaign_info['logo_path']):
            try:
                logo_img = Image(campaign_info['logo_path'])
                original_width = logo_img.imageWidth
                original_height = logo_img.imageHeight
                aspect_ratio = original_width / original_height
                
                max_width = 2*inch
                calculated_height = max_width / aspect_ratio
                max_height = 1.5*inch
                
                if calculated_height > max_height:
                    calculated_height = max_height
                    calculated_width = calculated_height * aspect_ratio
                else:
                    calculated_width = max_width
                
                logo = Image(campaign_info['logo_path'], width=calculated_width, height=calculated_height)
                logo.hAlign = 'CENTER'
                self.story.append(logo)
                self.story.append(Spacer(1, 10))
            except Exception as e:
                print(f"Warning: Could not load logo: {e}")
                # Fallback to text branding
                digiad_style = ParagraphStyle(
                    'DigiAdBrand',
                    parent=self.styles['Normal'],
                    fontSize=18,
                    fontName='Times-Bold',
                    textColor=colors.HexColor('#1E40AF'),
                    alignment=1,
                    spaceAfter=20
                )
                digiad_brand = Paragraph("DigiAd", digiad_style)
                self.story.append(digiad_brand)
        else:
            # Add DigiAd text branding if no logo
            digiad_style = ParagraphStyle(
                'DigiAdBrand',
                parent=self.styles['Normal'],
                fontSize=18,
                fontName='Times-Bold',
                textColor=colors.HexColor('#1E40AF'),
                alignment=1,
                spaceAfter=20
            )
            digiad_brand = Paragraph("DigiAd", digiad_style)
            self.story.append(digiad_brand)

        # self.story.append(Spacer(1, 10))

        # Greeting
        client_name = campaign_info.get('customer_name', '[Client Name]')
        # greeting = Paragraph(f"Dear <b>{client_name},</b>", greeting_style)
        # self.story.append(greeting)
        self.story.append(Paragraph(f"{report_title}", section_header_style))
        self.story.append(Spacer(1, 10))

        # Prepare platform list for the body text
        platforms_text = ""
        if campaign_info.get('platforms'):
            if isinstance(campaign_info.get('platforms'), list):
                if len(campaign_info['platforms']) == 1:
                    platforms_text = campaign_info['platforms'][0]
                elif len(campaign_info['platforms']) == 2:
                    platforms_text = " and ".join(campaign_info['platforms'])
                else:
                    platforms_text = ", ".join(campaign_info['platforms'][:-1]) + ", and " + campaign_info['platforms'][-1]
            else:
                platforms_text = str(campaign_info.get('platforms'))
        else:
            platforms_text = '[Platform List]'

        campaign_name = campaign_info.get('campaign_name', '[Campaign Name]')

        # First paragraph
        first_para = f"Dear <b>{client_name},</b> We are delighted to present the campaign performance report for your recent campaign, <b>{campaign_name}</b>. This report provides a detailed overview of how the campaign performed across the platforms — <b>{platforms_text}</b>."
        self.story.append(Paragraph(first_para, body_style))
        
        self.story.append(Spacer(1, 2))
            # Format dates nicely
         # Format dates nicely
        start_date = campaign_info.get('start_date', 'N/A')
        end_date = campaign_info.get('end_date', 'N/A')
        
        # Try to format dates if they're in YYYY-MM-DD format
        formatted_start_date = start_date
        formatted_end_date = end_date
        try:
            from datetime import datetime
            if start_date != 'N/A':
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                formatted_start_date = start_date_obj.strftime('%B %d, %Y')
            if end_date != 'N/A':
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                formatted_end_date = end_date_obj.strftime('%B %d, %Y')
        except:
            pass  # Keep original format if parsing fails
        
        # Calculate campaign duration
        duration_text = ""
        try:
            if campaign_info.get('start_date') and campaign_info.get('end_date'):
                start_obj = datetime.strptime(campaign_info['start_date'], '%Y-%m-%d')
                end_obj = datetime.strptime(campaign_info['end_date'], '%Y-%m-%d')
                duration_days = (end_obj - start_obj).days + 1
                duration_text = f" ({duration_days} days)"
        except:
            pass
        
        # Create campaign details content
        brand_name = campaign_info.get('brand_name', 'N/A')
        objective = campaign_info.get('objective', 'N/A')
        campaign_details_para = f"The campaign was designed specifically for <b>{brand_name}</b> with the primary objective of driving <b>{objective}</b>. Running from <b>{formatted_start_date}</b> to <b>{formatted_end_date}</b>{duration_text}, this strategic initiative was crafted to maximize engagement and deliver measurable results across all selected advertising platforms."
        self.story.append(Paragraph(campaign_details_para, body_style))
        # Third paragraph
        second_para = "Within this report, you will find key performance metrics such as impressions, clicks, reach, and spend, presented in a clear and structured format. These insights are designed to highlight what worked well, identify opportunities for improvement, and guide your future campaign strategies."
        self.story.append(Paragraph(second_para, body_style))

        third_para = """Our analysis includes detailed breakdowns by platform, audience segments, and campaign phases, 
        along with actionable recommendations to optimize your advertising investment and maximize return on ad spend (ROAS) 
        for future campaigns."""
        
        # self.story.append(Paragraph(third_para, body_style))

        # self.story.append(Spacer(1, 5))
        # Add campaign-level insights and actions if available



        if campaign_data:
            # Add HTML Insights and Actions
            self.add_horizontal_line()

            if 'html_insights_and_actions' in campaign_data and campaign_data['html_insights_and_actions']:
                html_data = campaign_data['html_insights_and_actions']
                
                # print(f"\n\n\nData in the campaign insights and actions: {html_data}\n\n")
                # Add section header
                self.story.append(Paragraph("✧ Campaign Summary", self.section_heading_style))
                
                # Add insights if available
                if 'insights' in html_data and html_data['insights']:
                    self.story.append(Paragraph("➢ <b>Performance Insights:</b>", insight_style))
                    for insight in html_data['insights']:
                        insight_text = f"• {insight}"
                        self.story.append(Paragraph(insight_text, insight_style))
                
                
                # Add actions if available
                if 'actions' in html_data and html_data['actions']:
                    self.story.append(Spacer(1, 10))
                    self.story.append(Paragraph("➢ <b>Recommended Actions:</b>", insight_style))
                    for action in html_data['actions']:
                        action_text = f"• {action}"
                        self.story.append(Paragraph(action_text, insight_style))
            # self.add_horizontal_line()
            # self.story.append(Spacer(1, 10))

            # Add Campaign Level Summary
            if 'campaign_level' in campaign_data and campaign_data['campaign_level']:
                campaign_level_data = campaign_data['campaign_level']
                
                # Add section header
                # self.story.append(Paragraph("✧ Campaign Overview", self.section_heading_style))
                
                # # Add insights if available
                # if 'insights' in campaign_level_data and campaign_level_data['insights']:
                #     self.story.append(Paragraph("➣ <b>Key Insights:</b>", insight_style))
                #     for insight in campaign_level_data['insights']:
                #         insight_text = f"• {insight}"
                #         self.story.append(Paragraph(insight_text, insight_style))
                
                # # Add actions if available
                # if 'actions' in campaign_level_data and campaign_level_data['actions']:
                #     self.story.append(Spacer(1, 10))
                #     self.story.append(Paragraph("➣ <b>Recommended Actions:</b>", insight_style))
                #     for action in campaign_level_data['actions']:
                #         action_text = f"• {action}"
                #         self.story.append(Paragraph(action_text, insight_style))


            # Remove the insights and actions data from campaign_data after rendering
            if 'html_insights_and_actions' in campaign_data:
                del campaign_data['html_insights_and_actions']
            if 'campaign_level' in campaign_data:
                del campaign_data['campaign_level']
                    # Add navigation section for platforms
        if platforms_list:
            self.add_horizontal_line()
            self.add_navigation_section(platforms_list)
        

        # Add some space before the footer
        # self.story.append(Spacer(1, 20))

        # Add generated date footer
        # generated_style = ParagraphStyle(
            # 'Generated',
            # parent=self.styles['Normal'],
            # fontSize=10,
            # fontName='Helvetica-Oblique',
            # textColor=colors.grey,
            # alignment=1  # Center alignment
        # )
        
        # generated_date = datetime.datetime.now().strftime("%B %d, %Y")
        
        # self.story.append(Spacer(1, -5))
        # self.story.append(Paragraph(f"DigiAd | www.digiad.ai | Report Generated on {generated_date}", generated_style))

        # Add page break to separate first page from content
        self.add_page_break()
    
    def add_summary(self, summary_points: List[str],title="Key Insights"):
        """
        Add insights summary section with bullet points
        
        Args:
            summary_points: List of insight strings to display as bullet points
        """
        # Add "Key Insights" heading
        
        # Style for the bullet point text
        insights_bullet_style = ParagraphStyle(
            'InsightsBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=4,
            spaceBefore=0,
            leading=14,
            leftIndent=30,
            firstLineIndent=-10,
            bulletIndent=20,
            textColor=colors.HexColor("#000000"),  # Dark gray
            fontName='Times-Roman'
        )
        
        self.story.append(Paragraph(title, self.section_heading_style))
        
        # Add each bullet point
        for point in summary_points:
            bullet_text = f"• {point}"
            self.story.append(Paragraph(bullet_text, insights_bullet_style))
        
        # self.story.append(Spacer(1, 15))
   
    def add_insights_section(self, insights_list):
        """
        Add insights section with proper formatting
        
        Args:
            insights_list: List of insight strings
        """
        if not insights_list:
            return
        
        # Add insights title
        title_style = ParagraphStyle(
            'InsightTitle',
            parent=getSampleStyleSheet()['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            spaceAfter=8,
            leftIndent=0
        )
        
        title_para = Paragraph("✧ Key Insights:", title_style)
        self.story.append(title_para)
        
        # Add each insight as a bullet point
        insight_style = ParagraphStyle(
            'InsightText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            leftIndent=15,
            bulletIndent=10,
            spaceAfter=4
        )
        
        for insight in insights_list:
            if insight and insight.strip():
                # Clean the insight text and add bullet
                clean_insight = insight.strip()
                bullet_para = Paragraph(f"• {clean_insight}", insight_style)
                self.story.append(bullet_para)
        
        self.story.append(Spacer(1, 4))

    def add_actions_section(self, actions_list):
        """
        Add actions section with proper formatting
        
        Args:
            actions_list: List of action strings
        """
        if not actions_list:
            return
        
        # Add actions title
        title_style = ParagraphStyle(
            'ActionTitle',
            parent=getSampleStyleSheet()['Heading3'],
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            spaceAfter=8,
            leftIndent=0
        )
        
        title_para = Paragraph("✧ Recommended Actions:", title_style)
        self.story.append(title_para)
        
        # Add each action as a bullet point
        action_style = ParagraphStyle(
            'ActionText',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.black,
            leftIndent=15,
            bulletIndent=10,
            spaceAfter=4
        )
        
        for action in actions_list:
            if action and action.strip():
                # Clean the action text and add bullet
                clean_action = action.strip()
                bullet_para = Paragraph(f"• {clean_action}", action_style)
                self.story.append(bullet_para)
        
        # self.story.append(Spacer(1, 8))


def cleanup_figures(figures_list):
    """
    Clean up matplotlib figures after PDF generation is complete
    
    Args:
        figures_list: List of matplotlib figure objects to close
    """
    for fig in figures_list:
        if fig is not None:
            plt.close(fig)
    plt.clf()


def generate_report_pdf(
                        campaign_info: Dict[str, Any],
                        platforms_data: Dict[str, Dict],
                        max_table_rows: int = 10,
                        show_top_and_bottom: bool = True
                        ):
    """
    Create a comprehensive PDF report for multiple platforms with their respective data
    
    Args:
        campaign_info: Dictionary containing campaign details for the first page
        platforms_data: Dictionary with platform names as keys and data dictionaries as values
                      Format: {
                          'Platform1': {
                              'dataframes': [df1, df2, df3],
                              'df_titles': ['Table 1', 'Table 2', 'Table 3'],
                              'df_descriptions': ['Description 1', 'Description 2', 'Description 3'],  # Optional
                              'figures': [fig1, fig2],
                              'figure_titles': ['Chart 1', 'Chart 2'],
                              'image_paths': ['path1.png', 'path2.png'],  # Optional
                              'image_titles': ['Image 1', 'Image 2'],     # Optional
                              'insights': ['insight1', 'insight2'],       # Optional - Platform level (deprecated)
                              'actions': ['action1', 'action2'],          # Optional - Platform level (deprecated)
                              'plot_insights': ['plot1_insight', 'plot2_insight'],  # NEW - Plot specific insights
                              'plot_actions': ['plot1_action', 'plot2_action']      # NEW - Plot specific actions
                          },
                          'Platform2': { ... }
                      }
        max_table_rows: Maximum rows to show in each table (will show top and bottom if truncated)
        show_top_and_bottom: Whether to show both top and bottom segments when tables are truncated
    """
    
    campaign_name = campaign_info.get('campaign_name', 'campaign_report')
    filename = generate_fle_name(campaign_name)

    # Initialize PDF generator
    pdf_gen = FlexiblePDFGenerator(filename)
    platforms_list = campaign_info.get('platforms', [])
    
    # Add campaign first page
    pdf_gen.add_campaign_first_page(campaign_info, campaign_data=platforms_data, 
                                   platforms_list=platforms_list)
    
    for platform_idx, (platform_name, data) in enumerate(platforms_data.items()):

        if platform_idx > 0:
            pdf_gen.add_page_break()
        
        # Add platform heading
        pdf_gen.add_platform_heading(f"{platform_name} Analytics", platform_name=platform_name)
        pdf_gen.add_horizontal_line(thickness=0.5, color=colors.black, 
                                        spaceBefore=0)
        
        pdf_gen.add_spacer(10)
        
        # Get platform data
        dataframes = data.get('dataframes', [])
        df_titles = data.get('df_titles', [f"Table {i+1}" for i in range(len(dataframes))])
        df_descriptions = data.get('df_descriptions', [None] * len(dataframes))
        figures = data.get('figures', [])
        figure_titles = data.get('figure_titles', [f"Chart {i+1}" for i in range(len(figures))])
        
        # NEW: Get plot-specific insights and actions
        plot_insights = data.get('plot_insights', [])
        plot_actions = data.get('plot_actions', [])
        
        # Keep platform-level insights for backward compatibility (will be added at end if no plot-specific insights)
        platform_insights = data.get('insights', [])
        platform_actions = data.get('actions', [])
        
        # Process items in pairs (2 tables + 2 graphs per page)
        max_items = max(len(dataframes), len(figures))
        
        for i in range(0, max_items, 2):
            # Get pairs of items
            df1 = dataframes[i] if i < len(dataframes) else None
            df2 = dataframes[i+1] if i+1 < len(dataframes) else None
            fig1 = figures[i] if i < len(figures) else None
            fig2 = figures[i+1] if i+1 < len(figures) else None

            # Get corresponding titles and descriptions
            table1_title = df_titles[i] if i < len(df_titles) else None
            table2_title = df_titles[i+1] if i+1 < len(df_titles) else None
            table1_description = df_descriptions[i] if i < len(df_descriptions) else None
            table2_description = df_descriptions[i+1] if i+1 < len(df_descriptions) else None
            fig1_title = figure_titles[i] if i < len(figure_titles) else None
            fig2_title = figure_titles[i+1] if i+1 < len(figure_titles) else None
            
            # NEW: Get plot-specific insights and actions for this pair
            insight1 = plot_insights[i] if i < len(plot_insights) else None
            insight2 = plot_insights[i+1] if i+1 < len(plot_insights) else None
            action1 = plot_actions[i] if i < len(plot_actions) else None
            action2 = plot_actions[i+1] if i+1 < len(plot_actions) else None

            # Add tables and graphs
            if df1 is not None and df2 is not None and fig1 is not None and fig2 is not None:
                pdf_gen.add_two_tables_and_side_by_side_graphs(
                    df1, df2, fig1, fig2,
                    table1_title, table2_title,
                    fig1_title, fig2_title,
                    table1_description, table2_description,
                    max_rows=max_table_rows, show_top_and_bottom=show_top_and_bottom
                )
            else:
                # Fallback to individual processing for remaining items
                if df1 is not None:
                    pdf_gen.add_dataframe(df1, title=table1_title, max_rows=max_table_rows, 
                                        description=table1_description, show_top_and_bottom=show_top_and_bottom)
                if df2 is not None:
                    pdf_gen.add_dataframe(df2, title=table2_title, max_rows=max_table_rows, 
                                        description=table2_description, show_top_and_bottom=show_top_and_bottom)
                if fig1 is not None:
                    pdf_gen.add_matplotlib_figure(fig1, title=fig1_title)
                if fig2 is not None:
                    pdf_gen.add_matplotlib_figure(fig2, title=fig2_title)

            # NEW: Add plot-specific insights and actions on the same page
            add_plot_insights_to_page(pdf_gen, insight1, action1, insight2, action2)

            # Check if this is the last set in platform
            is_last_set_in_platform = (i + 2 >= max_items)
    
            if not is_last_set_in_platform:
                pdf_gen.add_page_break()
                
        # NEW: Only add platform-level insights if no plot-specific insights were found
        if not plot_insights and platform_insights:
            pdf_gen.add_summary(platform_insights, title="Key Insights")
        if not plot_actions and platform_actions:
            pdf_gen.add_summary(platform_actions, title="Recommended Actions")
            
    # Generate final PDF
    pdf_gen.generate_pdf()
    cleanup_figures(figures)
    return pdf_gen.filename


def add_plot_insights_to_page(pdf_gen, insight1=None, action1=None, insight2=None, action2=None):
    """
    Add plot-specific insights and actions to the current page
    
    Args:
        pdf_gen: The PDF generator instance
        insight1: Insight for first plot (optional)
        action1: Action for first plot (optional)
        insight2: Insight for second plot (optional)
        action2: Action for second plot (optional)
    """
    
    # Add some spacing before insights section
    pdf_gen.add_spacer(15)
    
    # Collect all insights and actions that are not None/empty
    insights_to_add = []
    actions_to_add = []
    
    if insight1 and insight1.strip():
        insights_to_add.append(f"{insight1}")
    if insight2 and insight2.strip():
        insights_to_add.append(f"{insight2}")
        
    if action1 and action1.strip():
        actions_to_add.append(f"{action1}")
    if action2 and action2.strip():
        actions_to_add.append(f"{action2}")
    
    # Add insights section if we have any insights
    if insights_to_add:
        pdf_gen.add_insights_section(insights_to_add)
    
    # Add actions section if we have any actions
    if actions_to_add:
        pdf_gen.add_actions_section(actions_to_add)



